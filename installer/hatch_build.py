"""Hatch build hook: bundle the plugin catalogue into src/robotframework_plugins/_assets/.

The plugin trees under ``plugins/<name>/`` are the source of truth (they
are what the marketplace and the rf-skill-eval harness use). The
installer ships the *same* trees inside its wheel, one per plugin with
status ``active`` or ``deprecated`` in its ``catalog.yaml``:

    _assets/catalog.json          name, version, tier, status, summary, ...
    _assets/plugins/<name>/       the plugin tree

Rather than maintaining a duplicate copy in the package source, this
hook copies the trees at build time. Editable installs (`pip install -e
installer/`) also fire the hook the first time, populating the assets
dir for development.

Hatch invokes ``initialize`` before the build target runs.

Reference: https://hatch.pypa.io/latest/plugins/build-hook/custom/
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

# The path layout assumed:
#   <repo-root>/plugins/<name>/                ← canonical sources
#   <repo-root>/installer/                     ← this package; hatch_build.py lives here
#   <repo-root>/installer/src/robotframework_plugins/_assets/   ← bundle destination
#
# Hatch sets ``self.root`` to the directory containing pyproject.toml,
# i.e. ``<repo-root>/installer``. The plugin trees therefore sit one
# level up.
PLUGINS_REL = Path("..") / "plugins"
ASSETS_REL = Path("src") / "robotframework_plugins" / "_assets"
_IGNORE_ANYWHERE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", ".pytest_cache", ".mypy_cache", ".ruff_cache", "*.egg-info",
)
CATALOG_SRC_REL = Path("src") / "robotframework_plugins" / "_catalog.py"


def _load_catalog_module():
    """The package's ``_catalog`` module, loaded by path: the package isn't
    importable while its own wheel is being built. ``bundle.fetch()`` builds
    snapshot catalogues with the same code."""
    path = Path(__file__).resolve().parent / CATALOG_SRC_REL
    spec = importlib.util.spec_from_file_location("_robotframework_plugins_catalog", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_catalog = _load_catalog_module()
#: Re-exported for scripts and tests that read them from the hook.
BUNDLED_STATUSES = _catalog.BUNDLED_STATUSES
catalog_entries = _catalog.catalog_entries


def plugin_ignore(plugin_root: Path):
    """``copytree`` ignore for one plugin tree."""
    root = plugin_root.resolve()

    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored = set(_IGNORE_ANYWHERE(directory, names))
        if Path(directory).resolve() == root:
            ignored |= _catalog.PLUGIN_ONLY_DIRS & set(names)
        return ignored

    return ignore


class CustomBuildHook(BuildHookInterface):  # type: ignore[misc]
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        plugins_src = (Path(self.root) / PLUGINS_REL).resolve()
        assets_dst = (Path(self.root) / ASSETS_REL).resolve()

        # Build flow:
        #   1. sdist build   — runs from the repo, finds ../plugins/, copies
        #                      the bundled plugins into the package's _assets/
        #                      tree, and the sdist tarball includes _assets/.
        #   2. wheel build   — runs from an extracted sdist (no parent
        #                      `plugins/` available). Here we *skip* the
        #                      copy; _assets/ is already populated from
        #                      the sdist contents and is what we want
        #                      shipped in the wheel.
        if not plugins_src.is_dir():
            if (assets_dst / "catalog.json").is_file() and any(assets_dst.rglob("SKILL.md")):
                self.app.display_info(
                    f"robotframework-plugins: plugin sources not present at "
                    f"{plugins_src} but _assets/ is already populated "
                    f"({_count_files(assets_dst)} files) — assuming "
                    f"sdist→wheel build, skipping the bundle step"
                )
                return
            raise FileNotFoundError(
                f"plugin sources not found at {plugins_src} and no "
                f"populated _assets/ tree at {assets_dst}; cannot build "
                f"the robotframework-plugins wheel without the bundled assets"
            )

        entries = catalog_entries(plugins_src)

        # Wipe the previous bundle so removed files don't linger in the
        # wheel. Use ignore_errors=True because on some filesystems the
        # dir might not exist yet.
        if assets_dst.exists():
            shutil.rmtree(assets_dst, ignore_errors=True)
        assets_dst.mkdir(parents=True)
        for entry in entries:
            src = plugins_src / entry["name"]
            shutil.copytree(src, assets_dst / "plugins" / entry["name"], ignore=plugin_ignore(src))
        (assets_dst / "catalog.json").write_text(_catalog.catalog_document(entries), encoding="utf-8")
        self.app.display_info(
            f"robotframework-plugins: bundled {', '.join(e['name'] for e in entries)} → {assets_dst} "
            f"({_count_files(assets_dst)} files)"
        )


def _count_files(root: Path) -> int:
    return sum(1 for p in root.rglob("*") if p.is_file())
