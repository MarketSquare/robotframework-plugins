#!/usr/bin/env python3
"""Decide whether a PR has the approvals it needs (spec plugin-trust-tiers,
"Every change is reviewed by an owner of the plugin"; design D9).

CODEOWNERS can require one approval per path; this check requires one from
each group a change concerns:
  - owners:<plugin>  a maintainer of each plugin the PR touches (the base
                     branch's ``catalog.yaml``, so a PR can't approve itself in);
  - foundation       a Foundation reviewer when a touched plugin is ``verified``
                     on either side, or the PR promotes one to ``verified``;
  - security         a security reviewer when a security-relevant path changes
                     (``.github/governance.yaml``), or a SKILL.md's
                     ``allowed-tools`` line.
The PR author's own approval never counts, and only each reviewer's latest
review state does.

Input is a PR snapshot (JSON) that the workflow builds from the API:
  {"author": "login",
   "files": [{"filename": "...", "patch": "..."}],
   "reviews": [{"user": "login", "state": "APPROVED", "submitted_at": "..."}],
   "base_catalogs": {"rf-web": "<catalog.yaml text or parsed>"}, "head_catalogs": {...},
   "teams": {"foundation": ["login", ...], "security": ["login", ...]}}

Usage: scripts/required-reviews.py SNAPSHOT.json [--summary FILE] [--root DIR]
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TOOLS = re.compile(r"^[+-]\s*allowed-tools\s*:", re.MULTILINE)


@dataclass
class Group:
    name: str
    reasons: list[str] = field(default_factory=list)
    members: set[str] = field(default_factory=set)
    approved_by: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.approved_by)


def governance(root: Path) -> dict:
    return yaml.safe_load((root / ".github" / "governance.yaml").read_text(encoding="utf-8")) or {}


def security_relevant(file: dict, patterns: list[str]) -> bool:
    name = file["filename"]
    if any(fnmatch.fnmatch(name, p) for p in patterns):
        return True
    return name.endswith("/SKILL.md") and bool(ALLOWED_TOOLS.search(file.get("patch") or ""))


def touched_plugins(files: list[dict]) -> set[str]:
    out = set()
    for f in files:
        parts = f["filename"].split("/")
        if len(parts) > 2 and parts[0] in ("plugins", "bundles"):
            out.add(parts[1])
    return out


def approvals(reviews: list[dict], author: str) -> set[str]:
    latest: dict[str, tuple[str, str]] = {}
    for r in reviews:
        user, state, when = r.get("user"), str(r.get("state", "")).upper(), str(r.get("submitted_at") or "")
        if not user or state == "COMMENTED":
            continue
        if user not in latest or when >= latest[user][1]:
            latest[user] = (state, when)
    return {u for u, (state, _) in latest.items() if state == "APPROVED" and u != author}


def _catalogs(raw: dict) -> dict[str, dict]:
    """Catalogs as parsed dicts; the workflow passes the YAML text."""
    return {name: (yaml.safe_load(c) or {}) if isinstance(c, str) else (c or {}) for name, c in (raw or {}).items()}


def required_groups(snap: dict, gov: dict) -> list[Group]:
    files = snap.get("files") or []
    base, head = _catalogs(snap.get("base_catalogs")), _catalogs(snap.get("head_catalogs"))
    teams = snap.get("teams") or {}
    groups: list[Group] = []
    plugins = touched_plugins(files)
    for name in sorted(plugins):
        cat = base.get(name) or head.get(name)
        if cat is None:
            continue
        g = Group(f"owners:{name}", members={m["github"] for m in cat.get("maintainers") or []})
        g.reasons.append(f"changes plugins/{name}" + ("" if name in base else " (new plugin)"))
        groups.append(g)
    foundation = Group("foundation", members=set(teams.get("foundation") or []))
    for name in sorted(plugins | set(base) | set(head)):
        before, after = (base.get(name) or {}).get("tier"), (head.get(name) or {}).get("tier")
        if after == "verified" and before != "verified":
            foundation.reasons.append(f"promotes {name} to verified")
        elif name in plugins and "verified" in (before, after):
            foundation.reasons.append(f"changes verified plugin {name}")
    if foundation.reasons:
        groups.append(foundation)
    security = Group("security", members=set(teams.get("security") or []))
    patterns = gov.get("security_paths") or []
    security.reasons = [f["filename"] for f in files if security_relevant(f, patterns)]
    if security.reasons:
        groups.append(security)
    approved = approvals(snap.get("reviews") or [], str(snap.get("author") or ""))
    for g in groups:
        g.approved_by = sorted(approved & g.members)
    return groups


def summary(groups: list[Group], gov: dict) -> str:
    teams = gov.get("teams") or {}
    lines = ["## Required reviews", ""]
    if not groups:
        return "\n".join(lines + ["No plugin or security-relevant file changed; no group approval is required.", ""])
    lines += ["| Group | Why | Approved by |", "|---|---|---|"]
    for g in groups:
        label = f"@{teams[g.name]}" if g.name in teams else g.name
        why = "; ".join(g.reasons[:5]) + (f" (+{len(g.reasons) - 5} more)" if len(g.reasons) > 5 else "")
        lines.append(f"| {label} | {why} | {', '.join(g.approved_by) or '**missing**'} |")
    missing = [g.name for g in groups if not g.ok]
    lines += ["", "All required groups approved." if not missing else f"Waiting for: {', '.join(missing)}.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    gov = governance(args.root)
    groups = required_groups(json.loads(args.snapshot.read_text(encoding="utf-8")), gov)
    text = summary(groups, gov)
    if args.summary:
        args.summary.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if all(g.ok for g in groups) else 1


if __name__ == "__main__":
    sys.exit(main())
