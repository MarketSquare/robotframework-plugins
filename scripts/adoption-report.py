#!/usr/bin/env python3
"""Quarterly adoption report (spec adoption-reporting, "Quarterly adoption
report"; design D11).

Builds ``docs/reports/adoption-<YYYY>-Q<n>.md`` from public signals only:

  DATA/traffic/<date>/{views,clones}.json   GitHub traffic snapshots from the
                                            adoption-data branch (they overlap;
                                            each day counts once, latest wins)
  DATA/pypi.json        pypistats "overall" data for robotframework-plugins
  DATA/issues.json      issues: [{number, state, labels: [names], created_at, body}]
  DATA/evals.json       {plugin: [{release, date, score}]}, oldest first: the
                        narrow-tier pass rate of each plugin release's baseline
                        (``--evals-from-git`` builds it from <plugin>--v* tags)

Per plugin it shows feedback (helped / partly / didn't, from the feedback
form), open issues, the latest eval score and its trend, and lists candidates:

  demotion     a verified plugin whose eval score fell in each of its last two
               releases, or whose feedback is mostly negative (at least 3 answers)
  promotion    a community plugin with at least two maintainers, eval scores
               and no more negative than positive feedback
  deprecation  an active plugin without maintainers, or a community plugin
               whose latest eval score is below 0.5

Downloads are per package: every plugin ships in robotframework-plugins, so
the report gives the installer's downloads once instead of a per-plugin guess.

Usage: scripts/adoption-report.py --data DIR --quarter 2026-Q4 [--output FILE]
       [--root REPO] [--evals-from-git]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
HELPED = re.compile(r"^### Did the plugin help\?\s*\n+\s*(Yes|Partly|No)\s*$", re.MULTILINE)


def quarter_range(quarter: str) -> tuple[dt.date, dt.date]:
    m = re.fullmatch(r"(\d{4})-Q([1-4])", quarter)
    if not m:
        raise SystemExit(f"--quarter must look like 2026-Q4, not {quarter!r}")
    year, q = int(m.group(1)), int(m.group(2))
    start = dt.date(year, 3 * q - 2, 1)
    end = dt.date(year + (q == 4), 1 if q == 4 else 3 * q + 1, 1) - dt.timedelta(days=1)
    return start, end


def catalogs(root: Path) -> dict[str, dict]:
    return {p.parent.name: yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            for p in sorted((root / "plugins").glob("*/catalog.yaml"))}


def traffic(data: Path, start: dt.date, end: dt.date) -> dict[str, dict[dt.date, tuple[int, int]]]:
    """``{"views"|"clones": {day: (count, uniques)}}`` inside the quarter."""
    out: dict[str, dict[dt.date, tuple[int, int]]] = {"views": {}, "clones": {}}
    for snap in sorted((data / "traffic").glob("*/")):
        for kind in out:
            path = snap / f"{kind}.json"
            if not path.is_file():
                continue
            for row in json.loads(path.read_text(encoding="utf-8")).get(kind) or []:
                day = dt.date.fromisoformat(str(row["timestamp"])[:10])
                if start <= day <= end:
                    out[kind][day] = (int(row.get("count", 0)), int(row.get("uniques", 0)))
    return out


def downloads(data: Path, start: dt.date, end: dt.date) -> int | None:
    path = data / "pypi.json"
    if not path.is_file():
        return None
    rows = json.loads(path.read_text(encoding="utf-8")).get("data") or []
    return sum(int(r["downloads"]) for r in rows
               if r.get("category", "without_mirrors") == "without_mirrors"
               and start <= dt.date.fromisoformat(r["date"]) <= end)


def issues_by_plugin(data: Path, start: dt.date, end: dt.date, names: list[str]) -> dict[str, dict[str, int]]:
    out = {n: {"Yes": 0, "Partly": 0, "No": 0, "open": 0} for n in names}
    path = data / "issues.json"
    if not path.is_file():
        return out
    for issue in json.loads(path.read_text(encoding="utf-8")):
        labels = {lb if isinstance(lb, str) else lb.get("name") for lb in issue.get("labels") or []}
        plugins = [lb.split(":", 1)[1] for lb in labels if lb and lb.startswith("plugin:")]
        created = dt.date.fromisoformat(str(issue.get("created_at"))[:10])
        for name in plugins:
            if name not in out:
                continue
            if issue.get("state") == "open":
                out[name]["open"] += 1
            if "feedback" in labels and start <= created <= end:
                m = HELPED.search(issue.get("body") or "")
                if m:
                    out[name][m.group(1)] += 1
    return out


def narrow_score(baseline: dict) -> float | None:
    """Mean pass rate of the gating treatment entries of a narrow baseline."""
    rates = [e["pass_rate"] for e in (baseline.get("entries") or {}).values()
             if e.get("arm") == "treatment" and e.get("gating", True) and e.get("pass_rate") is not None]
    return round(sum(rates) / len(rates), 4) if rates else None


def evals_from_git(root: Path, names: list[str]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for name in names:
        tags = subprocess.run(["git", "tag", "--list", f"{name}--v*", "--sort=creatordate",
                               "--format=%(refname:short) %(creatordate:short)"],
                              cwd=root, capture_output=True, text=True, check=False).stdout.split("\n")
        for line in filter(None, tags):
            tag, date = line.split()
            show = subprocess.run(["git", "show", f"{tag}:plugins/{name}/evals/baselines/narrow.json"],
                                  cwd=root, capture_output=True, text=True, check=False)
            if show.returncode != 0:
                continue
            score = narrow_score(json.loads(show.stdout))
            if score is not None:
                out.setdefault(name, []).append({"release": tag.split("--v", 1)[1], "date": date, "score": score})
    return out


def candidates(cats: dict[str, dict], evals: dict[str, list[dict]],
               feedback: dict[str, dict[str, int]]) -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {"demotion": [], "promotion": [], "deprecation": []}
    for name, cat in cats.items():
        if cat.get("status") != "active":
            continue
        scores = [e["score"] for e in evals.get(name, [])]
        fb = feedback.get(name, {})
        pos, neg = fb.get("Yes", 0), fb.get("No", 0)
        answers = pos + neg + fb.get("Partly", 0)
        if cat.get("tier") == "verified":
            if len(scores) >= 3 and scores[-3] > scores[-2] > scores[-1]:
                out["demotion"].append((name, f"eval score fell for two releases ({scores[-3]:.0%} → "
                                              f"{scores[-2]:.0%} → {scores[-1]:.0%})"))
            elif answers >= 3 and neg > pos:
                out["demotion"].append((name, f"mostly negative feedback ({neg} of {answers} didn't help)"))
        elif len(cat.get("maintainers") or []) >= 2 and scores and neg <= pos:
            out["promotion"].append((name, f"two maintainers, eval score {scores[-1]:.0%}, feedback {pos}/{answers} helped"))
        if not cat.get("maintainers"):
            out["deprecation"].append((name, "no maintainer"))
        elif cat.get("tier") == "community" and scores and scores[-1] < 0.5:
            out["deprecation"].append((name, f"eval score {scores[-1]:.0%}"))
    return out


def _trend(scores: list[float]) -> str:
    if len(scores) < 2:
        return "–"
    delta = scores[-1] - scores[-2]
    return "steady" if abs(delta) < 0.005 else (f"up {delta:.0%}" if delta > 0 else f"down {-delta:.0%}")


def render(quarter: str, root: Path, data: Path, evals: dict[str, list[dict]]) -> str:
    start, end = quarter_range(quarter)
    cats = catalogs(root)
    listed = [n for n, c in cats.items() if c.get("status") in ("active", "deprecated")]
    tr = traffic(data, start, end)
    dl = downloads(data, start, end)
    fb = issues_by_plugin(data, start, end, listed)
    days = (end - start).days + 1
    lines = [
        f"# Adoption report {quarter}",
        "",
        f"{start.isoformat()} to {end.isoformat()}. Built from public signals only: GitHub traffic, PyPI "
        "downloads, issues and the committed eval baselines. The installer and the plugins send nothing.",
        "",
        "## Repository and package",
        "",
        "| Signal | Quarter |",
        "|---|---|",
    ]
    for kind in ("views", "clones"):
        counted = tr[kind]
        total = sum(c for c, _ in counted.values())
        if not counted:
            lines.append(f"| GitHub {kind} | no data |")
            continue
        cover = f" ({len(counted)} of {days} days recorded)" if len(counted) < days else ""
        lines.append(f"| GitHub {kind} | {total}{cover} |")
    lines.append(f"| PyPI downloads of robotframework-plugins | {dl if dl is not None else 'no data'} |")
    lines += [
        "",
        "Every plugin ships in the one PyPI package, so downloads aren't counted per plugin.",
        "",
        "## Plugins",
        "",
        "| Plugin | Tier | Status | Helped | Partly | Didn't | Open issues | Eval score | Trend |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for name in listed:
        cat, f = cats[name], fb[name]
        scores = [e["score"] for e in evals.get(name, [])]
        score = f"{scores[-1]:.0%}" if scores else "–"
        lines.append(f"| `{name}` | {cat.get('tier')} | {cat.get('status')} | {f['Yes']} | {f['Partly']} | "
                     f"{f['No']} | {f['open']} | {score} | {_trend(scores)} |")
    lines += ["", "## Candidates", ""]
    found = candidates({n: cats[n] for n in listed}, evals, fb)
    for kind, title in (("demotion", "Demotion"), ("promotion", "Promotion"), ("deprecation", "Deprecation")):
        items = found[kind]
        lines.append(f"**{title}:** " + ("; ".join(f"`{n}`, {why}" for n, why in items) if items else "none") + ".")
        lines.append("")
    lines.append("A candidate is a prompt for a maintainer decision, not a decision (see GOVERNANCE.md).")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--quarter", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--evals-from-git", action="store_true")
    args = parser.parse_args(argv)
    names = list(catalogs(args.root))
    evals_path = args.data / "evals.json"
    if args.evals_from_git:
        evals = evals_from_git(args.root, names)
    elif evals_path.is_file():
        evals = json.loads(evals_path.read_text(encoding="utf-8"))
    else:
        evals = {}
    text = render(args.quarter, args.root, args.data, evals)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
