"""Public Python API to the plugin content this package bundles.

    from robotframework_plugins import bundle

    bundle.CATALOG_FORMAT   # 1; changes only on a breaking change to catalog() entries
    bundle.catalog()        # the bundled plugins (active and deprecated)
    bundle.skills_dirs()    # {plugin: Path of its skills/ folder}, rf-core first
    bundle.fetch("main")    # opt-in: the same for a ref of the repository (network)

Only these names (and ``Snapshot``, ``FetchError``) are public; see the
"Python API" section of the README for the compatibility promise. Importing
this module, ``catalog()`` and ``skills_dirs()`` never use the network.
"""

from __future__ import annotations

import atexit
import copy
import shutil
import tempfile
import threading
from pathlib import Path
from typing import Any

from . import _assets
from ._catalog import CATALOG_FORMAT, skill_dirs
from ._snapshot import FetchError, Snapshot, fetch

__all__ = ("CATALOG_FORMAT", "FetchError", "Snapshot", "catalog", "fetch", "skills_dirs")

_lock = threading.Lock()
_extracted: Path | None = None


def catalog() -> list[dict[str, Any]]:
    """The bundled plugins (status active or deprecated), in catalogue order.

    Each entry has at least ``name``, ``version``, ``status``, ``tier``,
    ``summary``, ``libraries`` (``[{name, package, versions}]``),
    ``robotframework``, ``dependencies``, ``bundle`` and ``bundled``. The list
    is a copy: changing it doesn't change later results. Empty for a broken
    build without a catalogue.
    """
    return copy.deepcopy(_assets.bundled_catalog())


def skills_dirs() -> dict[str, Path]:
    """``{plugin name: absolute Path of its skills/ folder}``.

    Every active plugin that isn't a bundle and has skills, ``rf-core`` first,
    then catalogue order. The folders exist for the life of the process, also
    when the package is imported from a zip archive (then the bundle is copied
    once to a temporary folder, removed at exit).
    """
    entries = _assets.bundled_catalog()
    if not entries:
        return {}
    return skill_dirs(entries, _bundle_root())


def _bundle_root() -> Path:
    """The bundle (``_assets/``) as a real directory."""
    global _extracted
    root = _assets.bundle_root_traversable()
    if isinstance(root, Path):
        return root
    with _lock:
        if _extracted is None:
            target = Path(tempfile.mkdtemp(prefix="robotframework-plugins-bundle-"))
            atexit.register(shutil.rmtree, target, True)
            _copy_tree(root, target)
            _extracted = target
        return _extracted


def _copy_tree(src: Any, dest: Path) -> None:
    """Copy an importlib Traversable tree; works where ``as_file`` can't copy
    directories (Python 3.10 and 3.11)."""
    for child in src.iterdir():
        if child.is_dir():
            sub = dest / child.name
            sub.mkdir()
            _copy_tree(child, sub)
        else:
            (dest / child.name).write_bytes(child.read_bytes())
