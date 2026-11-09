#!/usr/bin/env python3
"""Export a plugin's skills as standalone skill folders.

``plugins/<plugin>/skills/`` is the only source of a skill. Inside a
plugin, SKILL.md runs bundled scripts as ``"${CLAUDE_SKILL_DIR}/scripts/x.py"``,
which Claude Code expands. Standalone copies (the release tarballs for
Codex, Copilot and other agents, and the Claude Desktop upload archives)
use the plain ``scripts/x.py`` form instead, as they did before the
root ``skills/`` copy was retired.

    python scripts/export-skills.py rf-core build/skills
    python scripts/export-skills.py all build/skills     # every plugin's skills

Bytecode caches are left out. The output directory is replaced.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

#: The plugin form of a script command, as plugin SKILL.md files write it.
_PLUGIN_SCRIPT = re.compile(r'(python|--script) "\$\{CLAUDE_SKILL_DIR\}/scripts/([a-z_]+\.py)"')


def standalone_skill_md(text: str) -> str:
    """SKILL.md text with plugin script commands turned back into ``scripts/x.py``."""
    return _PLUGIN_SCRIPT.sub(r"\1 scripts/\2", text)


def export_skills(skills_dir: Path, out: Path, *, replace: bool = True) -> list[str]:
    """Copy every skill under ``skills_dir`` to ``out``; return the skill names.

    With ``replace=False`` the skills are added to an existing ``out``."""
    if replace and out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    names = []
    for skill in sorted(p for p in skills_dir.iterdir() if (p / "SKILL.md").is_file()):
        shutil.copytree(skill, out / skill.name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        md = out / skill.name / "SKILL.md"
        md.write_text(standalone_skill_md(md.read_text(encoding="utf-8")), encoding="utf-8")
        names.append(skill.name)
    return names


def skills_dirs(root: Path, plugin: str) -> list[Path]:
    """``plugins/<plugin>/skills``, or every plugin's for ``all``."""
    if plugin == "all":
        return sorted(p for p in (root / "plugins").glob("*/skills") if p.is_dir())
    return [root / "plugins" / plugin / "skills"]


def export_plugins(root: Path, plugin: str, out: Path) -> list[str]:
    """Export one plugin's skills, or every plugin's (``all``), into ``out``."""
    if out.exists():
        shutil.rmtree(out)
    names: list[str] = []
    for skills_dir in skills_dirs(root, plugin):
        names += export_skills(skills_dir, out, replace=False)
    return names


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("plugin", help="plugin under plugins/ whose skills to export, or 'all'")
    ap.add_argument("out", type=Path, help="output directory (replaced)")
    ap.add_argument("--root", type=Path, default=REPO, help="repository root")
    args = ap.parse_args(argv)
    missing = [d for d in skills_dirs(args.root, args.plugin) if not d.is_dir()]
    if missing:
        print(f"error: {missing[0]} not found", file=sys.stderr)
        return 1
    names = export_plugins(args.root, args.plugin, args.out)
    print(f"exported {len(names)} skills from {args.plugin} to {args.out}")
    return 0 if names else 1


if __name__ == "__main__":
    sys.exit(main())
