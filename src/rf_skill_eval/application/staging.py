"""The plugin tree the harness stages for the treatment arm.

The content ships in several plugins (``plugins/rf-core``, ``rf-web``, …;
split-rf-agentskills). The runner stages one tree: the skills, subagents,
hooks and hook scripts of the chosen plugins, merged. By default that is
every plugin with content, which is what installing the ``rf-agentskills``
bundle gives and what the stored baselines were measured with.

The tree is built from ``plugins/`` each time, so it never lags behind an
edit (unlike the generated ``bundles/`` copies, which only CI checks).
"""

from __future__ import annotations

import atexit
import shutil
import tempfile
from collections.abc import Iterable
from pathlib import Path

#: What the staged tree takes from each plugin.
PARTS = ("skills", "agents", "hooks", "scripts", ".mcp.json")
_SKIP_DIRS = {"__pycache__", ".venv", "node_modules"}


def has_content(plugin_dir: Path) -> bool:
    """Ships a skill, a subagent or a hook (a bundle ships none)."""
    return (
        any((d / "SKILL.md").is_file() for d in (plugin_dir / "skills").glob("*"))
        or any((plugin_dir / "agents").glob("*.md"))
        or (plugin_dir / "hooks" / "hooks.json").is_file()
    )


def content_plugins(plugins_dir: Path) -> list[str]:
    """Names of the plugins under ``plugins_dir`` that have content."""
    if not plugins_dir.is_dir():
        return []
    return sorted(p.name for p in plugins_dir.iterdir() if p.is_dir() and has_content(p))


def merge_plugins(plugins_dir: Path, out: Path, names: Iterable[str] | None = None) -> Path:
    """Merge the content of ``names`` (default: every content plugin) into ``out``.

    Raises ``ValueError`` for an unknown plugin or when two plugins ship the
    same file.
    """
    chosen = list(names) if names is not None else content_plugins(plugins_dir)
    unknown = [n for n in chosen if not (plugins_dir / n).is_dir()]
    if unknown:
        raise ValueError(f"unknown plugin(s) {unknown} under {plugins_dir}")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    owner: dict[Path, str] = {}
    for name in chosen:
        src = plugins_dir / name
        for part in PARTS:
            part_src = src / part
            if part_src.is_file():
                files = [part_src]
            elif part_src.is_dir():
                files = [f for f in part_src.rglob("*") if f.is_file() and f.suffix != ".pyc"
                         and not _SKIP_DIRS.intersection(f.relative_to(part_src).parts)]
            else:
                continue
            for f in files:
                rel = f.relative_to(src)
                if rel in owner:
                    raise ValueError(f"{rel.as_posix()} is shipped by both {owner[rel]} and {name}")
                owner[rel] = name
                dst = out / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst)
    return out


def staged_tree(plugins_dir: Path, names: Iterable[str] | None = None) -> Path:
    """A merged tree in a temporary directory, removed when the process exits."""
    tmp = Path(tempfile.mkdtemp(prefix="rf-eval-plugins-"))
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)
    return merge_plugins(plugins_dir, tmp / "plugin", names)
