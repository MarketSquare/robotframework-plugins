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
#: The plugin adapters install when no other is named (tests, old callers).
DEFAULT_PLUGIN = "rf-agentskills"


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


def relative_to_assets(path: Path, plugin: str = DEFAULT_PLUGIN) -> Path:
    """Compute ``path`` relative to the plugin's asset root, raising if outside."""
    with asset_root_path(plugin) as root:
        return path.resolve().relative_to(root.resolve())
