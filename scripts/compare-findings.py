#!/usr/bin/env python3
"""Compare scanner SARIF with a plugin's reviewed baseline (spec
content-security-scanning, "The gate fails on new findings only"; design D8).

Each result is normalised to ``(scanner, rule, file, fingerprint)``. The
fingerprint hashes the scanner, rule, file and the finding's evidence text,
without line numbers, so a finding keeps its fingerprint when lines move
(SkillSpector's own finding ids change on every run).

The gate fails on:
  - a HIGH or CRITICAL finding that is not in the baseline;
  - a baseline entry that has expired, or whose expiry is more than 12 months
    after today, or that lacks a reason.
MEDIUM and lower findings are reported, never fatal.

Usage:
  compare-findings.py --baseline security/baselines/rf-core.yaml \\
      --sarif skillspector=out/ss.sarif@plugins/rf-core \\
      --sarif cisco=out/cisco.sarif --summary out/summary.md

``@BASE`` names the folder the scanner ran in when its SARIF paths are
relative to it. ``--draft FILE`` writes baseline entries for every finding
not in the baseline yet, to review by hand (task 5.3).
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

FATAL = {"CRITICAL", "HIGH"}
ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
LEVEL_SEVERITY = {"error": "HIGH", "warning": "MEDIUM", "note": "LOW", "none": "INFO"}
MAX_EXPIRY_DAYS = 366


@dataclass(frozen=True)
class Finding:
    scanner: str
    rule: str
    file: str
    fingerprint: str
    severity: str
    line: int | None
    message: str

    @property
    def key(self) -> tuple[str, str, str, str]:
        return (self.scanner, self.rule, self.file, self.fingerprint)


@dataclass
class Result:
    new: list[Finding] = field(default_factory=list)
    accepted: list[tuple[Finding, dict]] = field(default_factory=list)
    unused: list[dict] = field(default_factory=list)
    invalid: list[tuple[dict, str]] = field(default_factory=list)

    @property
    def failed(self) -> list[Finding]:
        return [f for f in self.new if f.severity in FATAL]

    @property
    def ok(self) -> bool:
        return not self.failed and not self.invalid


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def fingerprint(scanner: str, rule: str, file: str, evidence: str) -> str:
    raw = "\x1f".join((scanner, rule, file, _norm(evidence)))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _path(uri: str, base: str) -> str:
    """Repository-relative path of a SARIF artifact URI."""
    uri = re.sub(r"^file://", "", uri)
    if uri.startswith("/"):
        with contextlib.suppress(ValueError):
            uri = Path(uri).resolve().relative_to(Path.cwd().resolve()).as_posix()
    while uri.startswith("./"):
        uri = uri[2:]
    base = base.strip("/")
    if base and not (uri == base or uri.startswith(base + "/")):
        uri = f"{base}/{uri}" if uri else base
    return uri


def _severity(result: dict) -> str:
    props = result.get("properties") or {}
    sev = str(props.get("severity") or props.get("security-severity-level") or "").upper()
    if sev in ORDER:
        return sev
    return LEVEL_SEVERITY.get(str(result.get("level") or "warning"), "MEDIUM")


def _evidence(result: dict) -> str:
    props = result.get("properties") or {}
    parts = [str(props.get(k) or "") for k in ("finding", "pattern")]
    for loc in result.get("locations") or []:
        snippet = ((loc.get("physicalLocation") or {}).get("region") or {}).get("snippet") or {}
        parts.append(str(snippet.get("text") or ""))
    parts.append(str((result.get("message") or {}).get("text") or ""))
    return " | ".join(p for p in parts if p)


def read_sarif(scanner: str, path: Path, base: str = "") -> list[Finding]:
    data = json.loads(path.read_text(encoding="utf-8") or '{"runs": []}')
    out = []
    for run in data.get("runs") or []:
        for result in run.get("results") or []:
            rule = str(result.get("ruleId") or "unknown")
            locs = result.get("locations") or [{}]
            phys = locs[0].get("physicalLocation") or {}
            file = _path(str((phys.get("artifactLocation") or {}).get("uri") or ""), base)
            line = (phys.get("region") or {}).get("startLine")
            out.append(Finding(
                scanner=scanner, rule=rule, file=file,
                fingerprint=fingerprint(scanner, rule, file, _evidence(result)),
                severity=_severity(result), line=line,
                message=_norm(str((result.get("message") or {}).get("text") or ""))[:160],
            ))
    return out


def load_baseline(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("entries") or [])


def _entry_problem(entry: dict, today: dt.date) -> str | None:
    for key in ("scanner", "rule", "file", "fingerprint", "reason", "reviewed_by", "expires"):
        if not str(entry.get(key) or "").strip():
            return f"missing {key}"
    expires = entry["expires"]
    if not isinstance(expires, dt.date):
        try:
            expires = dt.date.fromisoformat(str(expires))
        except ValueError:
            return f"expires is not a date: {expires!r}"
    if expires < today:
        return f"expired on {expires.isoformat()}"
    if (expires - today).days > MAX_EXPIRY_DAYS:
        return f"expires {expires.isoformat()}, more than 12 months away"
    return None


def compare(findings: list[Finding], baseline: list[dict], today: dt.date) -> Result:
    res = Result()
    entries: dict[tuple, dict] = {}
    for entry in baseline:
        problem = _entry_problem(entry, today)
        if problem:
            res.invalid.append((entry, problem))
            continue
        entries[(entry["scanner"], entry["rule"], entry["file"], str(entry["fingerprint"]))] = entry
    used = set()
    for f in findings:
        entry = entries.get(f.key)
        if entry is None:
            res.new.append(f)
        else:
            res.accepted.append((f, entry))
            used.add(f.key)
    res.unused = [e for k, e in entries.items() if k not in used]
    return res


def _row(f: Finding) -> str:
    where = f"{f.file}:{f.line}" if f.line else f.file
    return f"| {f.severity} | {f.scanner} | `{f.rule}` | `{where}` | {f.message.replace('|', '/')} |"


def summary(res: Result, plugin: str) -> str:
    verdict = "passed" if res.ok else "failed"
    lines = [f"## Security gate: {plugin}, {verdict}", ""]
    lines.append(
        f"{len(res.failed)} new HIGH or CRITICAL, {len(res.new) - len(res.failed)} new below HIGH, "
        f"{len(res.accepted)} accepted from the baseline, {len(res.invalid)} baseline problem(s)."
    )
    head = ["", "| Severity | Scanner | Rule | File | Message |", "|---|---|---|---|---|"]
    if res.invalid:
        lines += ["", "### Baseline problems", ""]
        lines += [f"- `{e.get('scanner')}` `{e.get('rule')}` `{e.get('file')}`: {p}" for e, p in res.invalid]
    for title, items in (("New findings that fail the gate", res.failed),
                         ("New findings below HIGH (reported only)", [f for f in res.new if f.severity not in FATAL])):
        if items:
            lines += ["", f"### {title}", *head]
            lines += [_row(f) for f in sorted(items, key=lambda f: (ORDER.index(f.severity), f.file, f.line or 0))]
    if res.accepted:
        lines += ["", "### Accepted findings", "", "| Scanner | Rule | File | Reason |", "|---|---|---|---|"]
        lines += [f"| {f.scanner} | `{f.rule}` | `{f.file}` | {str(e['reason']).replace('|', '/')} |" for f, e in res.accepted]
    if res.unused:
        lines += ["", f"{len(res.unused)} baseline entr{'y' if len(res.unused) == 1 else 'ies'} matched no finding "
                  "and can be removed."]
    return "\n".join(lines) + "\n"


def draft(res: Result, plugin: str) -> str:
    entries = [{
        "scanner": f.scanner, "rule": f.rule, "file": f.file, "fingerprint": f.fingerprint,
        "severity": f.severity, "line": f.line, "message": f.message,
        "reason": "", "reviewed_by": "", "expires": "",
    } for f in sorted(res.new, key=lambda f: (f.file, f.line or 0, f.rule))]
    return yaml.safe_dump({"plugin": plugin, "entries": entries}, sort_keys=False, allow_unicode=True, width=120)


def _sarif_arg(value: str) -> tuple[str, Path, str]:
    scanner, sep, rest = value.partition("=")
    if not sep or not rest:
        raise argparse.ArgumentTypeError(f"expected SCANNER=FILE[@BASE], got {value!r}")
    file, _, base = rest.partition("@")
    return scanner, Path(file), base


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--sarif", type=_sarif_arg, action="append", default=[], metavar="SCANNER=FILE[@BASE]")
    parser.add_argument("--summary", type=Path, help="write the Markdown summary here (default: stdout)")
    parser.add_argument("--draft", type=Path, help="write draft baseline entries for the new findings")
    parser.add_argument("--plugin", default="", help="plugin name for the summary (default: the baseline's)")
    parser.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    args = parser.parse_args(argv)

    findings = [f for scanner, path, base in args.sarif for f in read_sarif(scanner, path, base)]
    baseline = load_baseline(args.baseline)
    plugin = args.plugin
    if not plugin and args.baseline.is_file():
        plugin = (yaml.safe_load(args.baseline.read_text(encoding="utf-8")) or {}).get("plugin", "")
    plugin = plugin or args.baseline.stem
    res = compare(findings, baseline, args.today)
    text = summary(res, plugin)
    if args.summary:
        args.summary.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    if args.draft:
        args.draft.write_text(draft(res, plugin), encoding="utf-8")
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
