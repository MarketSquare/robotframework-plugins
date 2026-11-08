#!/usr/bin/env python3
"""Build one upload-ready ZIP per skill for Claude Desktop / claude.ai.

Claude loads custom skills uploaded under Customize -> Skills -> Upload a
skill; each archive holds the skill folder at its root (``rf-browser/SKILL.md``
...). The archives are byte-identical to what ``rf-agentskills install
--agent claude-desktop`` writes (same builder, deterministic timestamps).

The skills come from ``plugins/<plugin>/skills/`` in their standalone form
(see ``scripts/export-skills.py``), the same as the release tarballs.

Usage::

    python scripts/build-skill-zips.py --out dist/skill-zips [--plugin rf-agentskills]
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "installer" / "src"))

from robotframework_plugins.skillzip import skill_zip_bytes  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plugin", default="rf-agentskills", help="plugin whose skills to archive")
    parser.add_argument("--skills", type=Path, help="standalone skills root (default: export --plugin)")
    parser.add_argument("--out", type=Path, required=True, help="output directory")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        skills = args.skills
        if skills is None:
            skills = Path(tmp) / "skills"
            _export().export_skills(REPO / "plugins" / args.plugin / "skills", skills)
        count = 0
        for skill_dir in sorted(p for p in skills.iterdir() if (p / "SKILL.md").is_file()):
            (args.out / f"{skill_dir.name}.zip").write_bytes(skill_zip_bytes(skill_dir))
            count += 1
    print(f"{count} skill archives in {args.out}")
    return 0 if count else 1


def _export():
    spec = importlib.util.spec_from_file_location("export_skills", REPO / "scripts" / "export-skills.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
