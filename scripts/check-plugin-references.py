#!/usr/bin/env python3
"""Check that text in a plugin names the plugin of every skill it doesn't ship.

Spec ``plugin-split``, "Content names the plugin of a skill it does not ship":
a line in ``plugins/<P>/`` that names a skill shipped by another plugin ``Q``
must also name ``Q`` on the same line (a table row is one line), for example
"`rf-browser` (plugin `rf-web`)". The reader may have ``P`` without ``Q``.

Checked: every text file of each plugin, except its ``tests/`` and ``evals/``
(repository QA), ``variants/`` (generated from ``agents/``) and ``CHANGELOG.md``
(history). A skill's frontmatter ``description`` is not checked: the listing
budget limits it, and agents list each skill with its plugin prefix. A line may
opt out with ``plugin-ref: ignore`` (for detection lists such as a hook's regex).

    python scripts/check-plugin-references.py            # exit 1 on findings
    python scripts/check-plugin-references.py --root DIR
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKIP_DIRS = {"tests", "evals", "variants", "__pycache__"}
#: Release history names skills as they were then.
SKIP_FILES = {"CHANGELOG.md"}
TEXT_SUFFIXES = {".md", ".mjs", ".js", ".py", ".json", ".toml", ".yaml", ".yml", ".txt", ".robot", ".resource"}
TOKEN = re.compile(r"(?<![\w/.-])rf-[a-z0-9]+(?:-[a-z0-9]+)*(?![\w-])")
IGNORE = "plugin-ref: ignore"


def owners(root: Path) -> dict[str, str]:
    """``{skill: plugin}`` for every ``plugins/*/skills/*/SKILL.md``."""
    return {md.parent.name: md.parent.parent.parent.name for md in sorted(root.glob("plugins/*/skills/*/SKILL.md"))}


def plugin_files(plugin_dir: Path) -> list[Path]:
    files = []
    for path in sorted(plugin_dir.rglob("*")):
        rel = path.relative_to(plugin_dir)
        if (path.is_file() and path.suffix in TEXT_SUFFIXES and not SKIP_DIRS & set(rel.parts)
                and path.name not in SKIP_FILES):
            files.append(path)
    return files


def findings(root: Path) -> list[str]:
    owner = owners(root)
    out: list[str] = []
    for plugin_dir in sorted(p for p in (root / "plugins").iterdir() if p.is_dir()):
        me = plugin_dir.name
        for path in plugin_files(plugin_dir):
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            in_frontmatter = path.name == "SKILL.md" and bool(lines) and lines[0] == "---"
            for no, line in enumerate(lines, 1):
                if in_frontmatter and no > 1 and line == "---":
                    in_frontmatter = False
                if IGNORE in line or (in_frontmatter and line.startswith("description:")):
                    continue
                for skill in sorted(set(TOKEN.findall(line))):
                    other = owner.get(skill)
                    if other is None or other == me:
                        continue
                    if not re.search(rf"(?<![\w-]){re.escape(other)}(?![\w-])", line):
                        rel = path.relative_to(root).as_posix()
                        out.append(f"{rel}:{no}: names {skill} without its plugin {other}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=REPO, help="repository root")
    args = ap.parse_args(argv)
    found = findings(args.root)
    for line in found:
        print(line)
    if found:
        print(f"{len(found)} reference(s) to another plugin's skill without the plugin name", file=sys.stderr)
        return 1
    print("plugin references: every cross-plugin skill reference names its plugin")
    return 0


if __name__ == "__main__":
    sys.exit(main())
