"""Where the catalogue's content lives, for tests that read more than one plugin.

Each skill and subagent ships in exactly one plugin under ``plugins/<name>/``
(spec ``plugin-split``). These helpers find them without naming the plugin.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = "rf-core"


def skill_mds(root: Path = ROOT) -> list[Path]:
    """Every ``plugins/*/skills/*/SKILL.md``, sorted by skill name."""
    return sorted(root.glob("plugins/*/skills/*/SKILL.md"), key=lambda p: p.parent.name)


def skill_names(root: Path = ROOT) -> set[str]:
    return {md.parent.name for md in skill_mds(root)}


def skill_dir(name: str, root: Path = ROOT) -> Path:
    """The folder of skill ``name``, in whichever plugin ships it."""
    found = [md.parent for md in skill_mds(root) if md.parent.name == name]
    if len(found) != 1:
        raise LookupError(f"skill {name!r} found {len(found)} times: {found}")
    return found[0]


def plugin_of(name: str, root: Path = ROOT) -> str:
    """The plugin that ships skill ``name``."""
    return skill_dir(name, root).parent.parent.name


def core(root: Path = ROOT) -> Path:
    """``plugins/rf-core``: subagents, hooks and hook scripts."""
    return root / "plugins" / CORE
