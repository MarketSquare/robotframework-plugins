#!/usr/bin/env python3
"""Ownership and tier evidence checks (spec plugin-trust-tiers).

1. CODEOWNERS agrees with ``catalog.yaml``: every plugin has a
   ``/plugins/<name>/`` line whose people are exactly its ``maintainers``
   (teams on the line are ignored), and no line names a plugin that doesn't
   exist ("CODEOWNERS drift").
2. A ``verified`` plugin has its evidence ("Verified without evals is
   refused"): at least two maintainers, one of them in the Foundation reviewers
   team (checked when ``--team-members`` gives the team), a trigger set and a
   narrow eval task for every skill, and committed narrow and trigger baselines.
   A bundle is verified when every plugin it bundles is.

Missing evidence covered by a dated ``tier_grace`` entry in
``.github/governance.yaml`` is reported as a warning until that date.

Usage: scripts/check-governance.py [--root DIR] [--today YYYY-MM-DD]
                                   [--team-members FILE.json]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE_REL = Path(".github/governance.yaml")
CODEOWNERS_REL = Path(".github/CODEOWNERS")


def catalogs(root: Path) -> dict[str, dict]:
    return {p.parent.name: yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            for p in sorted((root / "plugins").glob("*/catalog.yaml"))}


def codeowners(root: Path) -> dict[str, list[str]]:
    """``{path pattern: owners}``, in file order (later lines win on GitHub)."""
    out: dict[str, list[str]] = {}
    path = root / CODEOWNERS_REL
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            pattern, *owners = line.split()
            out[pattern] = [o.lstrip("@") for o in owners]
    return out


def ownership_problems(root: Path) -> list[str]:
    cats = catalogs(root)
    owners = codeowners(root)
    problems = []
    for name, cat in cats.items():
        maintainers = {m["github"] for m in cat.get("maintainers") or []}
        line = owners.get(f"/plugins/{name}/")
        if line is None:
            problems.append(f"CODEOWNERS has no /plugins/{name}/ line (maintainers: {', '.join(sorted(maintainers))})")
            continue
        people = {o for o in line if "/" not in o}
        if people != maintainers:
            problems.append(f"{name}: CODEOWNERS lists {', '.join(sorted(people)) or 'nobody'}, "
                            f"catalog.yaml maintainers are {', '.join(sorted(maintainers)) or 'nobody'}")
    for pattern in owners:
        m = re.match(r"^/plugins/([^/]+)/", pattern)
        if m and m.group(1) not in cats:
            problems.append(f"CODEOWNERS names {pattern}, but there is no plugin {m.group(1)}")
    return problems


def skills(root: Path, name: str) -> list[str]:
    return sorted(p.parent.name for p in (root / "plugins" / name / "skills").glob("*/SKILL.md"))


def _task_skills(root: Path, name: str) -> set[str]:
    out = set()
    for task in (root / "plugins" / name / "evals" / "tasks" / "narrow").glob("*.yaml"):
        data = yaml.safe_load(task.read_text(encoding="utf-8")) or {}
        if data.get("skill"):
            out.add(str(data["skill"]))
    return out


def missing_evidence(root: Path, name: str, cat: dict, foundation: set[str] | None) -> list[str]:
    """What a verified plugin lacks, as short evidence ids with detail."""
    missing = []
    maintainers = [m["github"] for m in cat.get("maintainers") or []]
    if len(maintainers) < 2:
        missing.append("second-maintainer: verified needs at least two maintainers")
    if foundation is not None and not set(maintainers) & foundation:
        missing.append("foundation-maintainer: no maintainer is in the Foundation reviewers team")
    if cat.get("bundle"):
        return missing
    evals = root / "plugins" / name / "evals"
    own = skills(root, name)
    no_triggers = [s for s in own if not (evals / "triggers" / f"{s}.yaml").is_file()]
    if no_triggers:
        missing.append(f"trigger-sets: no trigger set for {', '.join(no_triggers)}")
    tasks = _task_skills(root, name)
    no_tasks = [s for s in own if s not in tasks]
    if no_tasks:
        missing.append(f"eval-tasks: no narrow eval task for {', '.join(no_tasks)}")
    no_base = [b for b in ("narrow.json", "triggers.json") if not (evals / "baselines" / b).is_file()]
    if no_base:
        missing.append(f"baselines: no committed {', '.join(no_base)}")
    return missing


def tier_problems(root: Path, today: dt.date, foundation: set[str] | None) -> tuple[list[str], list[str]]:
    """(failures, warnings)."""
    gov = yaml.safe_load((root / GOVERNANCE_REL).read_text(encoding="utf-8")) if (root / GOVERNANCE_REL).is_file() else {}
    grace = (gov or {}).get("tier_grace") or []
    cats = catalogs(root)
    fails, warns = [], []
    for name, cat in cats.items():
        if cat.get("tier") != "verified":
            continue
        missing = missing_evidence(root, name, cat, foundation)
        for member in cat.get("bundle") or []:
            if cats.get(member, {}).get("tier") != "verified":
                missing.append(f"bundled-plugins: bundles {member}, which is not verified")
        for item in missing:
            key = item.split(":", 1)[0]
            entry = next((g for g in grace if name in (g.get("plugins") or []) and key in (g.get("missing") or [])), None)
            until = entry and entry.get("until")
            if isinstance(until, str):
                until = dt.date.fromisoformat(until)
            if entry and until and until >= today:
                warns.append(f"{name} (verified): {item} (grace until {until.isoformat()})")
            elif entry:
                fails.append(f"{name} (verified): {item} (grace ended {until})")
            else:
                fails.append(f"{name} (verified): {item}")
    return fails, warns


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    parser.add_argument("--team-members", type=Path,
                        help='JSON {"foundation": [logins]}; without it the Foundation membership is not checked')
    args = parser.parse_args(argv)
    foundation = None
    if args.team_members:
        foundation = set(json.loads(args.team_members.read_text(encoding="utf-8")).get("foundation") or [])
    fails = ownership_problems(args.root)
    tier_fails, warns = tier_problems(args.root, args.today, foundation)
    fails += tier_fails
    for w in warns:
        print(f"warning: {w}")
    for f in fails:
        print(f"error: {f}")
    if not fails:
        print(f"governance: ownership and tiers OK ({len(warns)} warning(s))")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
