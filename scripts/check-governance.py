#!/usr/bin/env python3
"""Tier evidence check (spec plugin-trust-tiers).

A ``verified`` plugin has its evidence ("Verified without evals is refused"):
a trigger set and a narrow eval task for every skill, and committed narrow and
trigger baselines.

The check decides from the repository tree alone: it doesn't count
maintainers, look at teams or depend on the date ("No governance check fails
because of the date"). The security gate and the keyword check, which
``verified`` also needs, are required checks on every PR.

Usage: scripts/check-governance.py [--root DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def catalogs(root: Path) -> dict[str, dict]:
    return {p.parent.name: yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            for p in sorted((root / "plugins").glob("*/catalog.yaml"))}


def skills(root: Path, name: str) -> list[str]:
    return sorted(p.parent.name for p in (root / "plugins" / name / "skills").glob("*/SKILL.md"))


def _task_skills(root: Path, name: str) -> set[str]:
    out = set()
    for task in (root / "plugins" / name / "evals" / "tasks" / "narrow").glob("*.yaml"):
        data = yaml.safe_load(task.read_text(encoding="utf-8")) or {}
        if data.get("skill"):
            out.add(str(data["skill"]))
    return out


def missing_evidence(root: Path, name: str, cat: dict) -> list[str]:
    """What a verified plugin lacks, as short evidence ids with detail."""
    missing = []
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


def tier_problems(root: Path) -> list[str]:
    cats = catalogs(root)
    fails = []
    for name, cat in cats.items():
        if cat.get("tier") != "verified":
            continue
        missing = missing_evidence(root, name, cat)
        fails += [f"{name} (verified): {item}" for item in missing]
    return fails


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    fails = tier_problems(args.root)
    for f in fails:
        print(f"error: {f}")
    if not fails:
        print("governance: tier evidence OK")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
