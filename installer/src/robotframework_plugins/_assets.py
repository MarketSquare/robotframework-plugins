"""Locate and read the bundled plugin tree at runtime.

The bundle lives at ``robotframework_plugins/_assets/`` inside the installed
wheel. We use ``importlib.resources.files`` (3.9+, stable in 3.12) so
the same code path works under:

* normal pip / pipx wheel installs
* PEP 660 editable installs
* zipapp / PyInstaller frozen builds
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any, Iterator

# Resource root inside the installed package. The build hook copies each
# bundled plugin to ``_assets/plugins/<name>/`` and writes
# ``_assets/catalog.json`` at wheel time.
_ASSETS_RESOURCE_NAME = "_assets"
#: The plugin an adapter plans when no other is named (tests, old callers):
#: ``rf-core`` ships the hooks and the subagents every install needs.
DEFAULT_PLUGIN = "rf-core"


def bundle_root_traversable():
    """Return the whole bundle (catalogue plus plugins) as an importlib Traversable."""
    return files("robotframework_plugins").joinpath(_ASSETS_RESOURCE_NAME)


def asset_root_traversable(plugin: str = DEFAULT_PLUGIN):
    """Return one bundled plugin tree as an importlib Traversable."""
    return bundle_root_traversable().joinpath("plugins", plugin)


@contextmanager
def asset_root_path(plugin: str = DEFAULT_PLUGIN) -> Iterator[Path]:
    """Yield one bundled plugin tree as a real ``Path``.

    ``importlib.resources.as_file`` extracts the resource into a
    temporary directory if it lives inside a zip / wheel; for normal
    on-disk installs (the common case) it returns the path directly.
    """
    with as_file(asset_root_traversable(plugin)) as p:
        yield Path(p)


def asset_files(*subpath_parts: str, plugin: str = DEFAULT_PLUGIN) -> Iterator[Path]:
    """Yield every file under ``_assets/plugins/<plugin>/<subpath>`` as a Path.

    Recurses into subdirectories. Useful for adapters that want to
    walk a category like ``skills/`` or ``agents/``.
    """
    with asset_root_path(plugin) as root:
        target = root.joinpath(*subpath_parts)
        if not target.exists():
            return
        if target.is_file():
            yield target
            return
        for child in sorted(target.rglob("*")):
            if child.is_file():
                yield child


def bundled_catalog() -> list[dict[str, Any]]:
    """The bundled plugins: name, version, tier, status, summary, libraries, ...

    Empty when the bundle has no catalogue (a broken build).
    """
    try:
        text = bundle_root_traversable().joinpath("catalog.json").read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return []
    return list(json.loads(text).get("plugins", []))


def is_bundle(entry: dict[str, Any]) -> bool:
    """A catalogue entry with no content of its own (``rf-agentskills`` since 4.0.0)."""
    return bool(entry.get("bundle"))


def expand_bundles(names: list[str], catalog: list[dict[str, Any]]) -> list[str]:
    """``names`` with every bundle replaced by the plugins it bundles.

    File mode copies content per plugin: installing the bundle means
    installing the plugins it ships a copy of. Order is kept; duplicates are dropped."""
    by_name = {p["name"]: p for p in catalog}
    out: list[str] = []

    def add(name: str, seen: frozenset[str]) -> None:
        entry = by_name.get(name, {})
        if is_bundle(entry) and name not in seen:
            for dep in entry.get("bundled", []):
                add(dep, seen | {name})
        elif name not in out:
            out.append(name)

    for name in names:
        add(name, frozenset())
    return out


def content_plugins() -> tuple[str, ...]:
    """Every active plugin with content in the bundled catalogue (what a plan
    covers when the caller names none); ``(DEFAULT_PLUGIN,)`` without a catalogue."""
    names = [p["name"] for p in bundled_catalog() if p.get("status") == "active" and not is_bundle(p)]
    if DEFAULT_PLUGIN in names:  # rf-core first: the others depend on it
        names.remove(DEFAULT_PLUGIN)
        names.insert(0, DEFAULT_PLUGIN)
    return tuple(names) or (DEFAULT_PLUGIN,)


def relative_to_assets(path: Path, plugin: str = DEFAULT_PLUGIN) -> Path:
    """Compute ``path`` relative to the plugin's asset root, raising if outside."""
    with asset_root_path(plugin) as root:
        return path.resolve().relative_to(root.resolve())
