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

import json
import shutil
from pathlib import Path
from typing import Any

import yaml
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
#: Statuses the installer bundles; ``removed`` plugins stay out.
BUNDLED_STATUSES = ("active", "deprecated")
_IGNORE_ANYWHERE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", ".pytest_cache", ".mypy_cache", ".ruff_cache", "*.egg-info",
)
#: Plugin tests and evals are for this repository's CI, not for users. Only a
#: plugin's own top-level folders: skills ship example ``tests/`` folders too.
_PLUGIN_ONLY = {"tests", "evals"}


def plugin_ignore(plugin_root: Path):
    """``copytree`` ignore for one plugin tree."""
    root = plugin_root.resolve()

    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored = set(_IGNORE_ANYWHERE(directory, names))
        if Path(directory).resolve() == root:
            ignored |= _PLUGIN_ONLY & set(names)
        return ignored

    return ignore


def catalog_entries(plugins_dir: Path) -> list[dict[str, Any]]:
    """One entry per bundled plugin, from its catalog.yaml and plugin.json."""
    entries = []
    for d in sorted(p for p in plugins_dir.iterdir() if p.is_dir()):
        manifest_path = d / "catalog.yaml"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"{manifest_path} missing; run scripts/build-catalog.py --check")
        m = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if m.get("status") not in BUNDLED_STATUSES:
            continue
        pj = json.loads((d / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        deps = [x if isinstance(x, str) else x["name"] for x in pj.get("dependencies", [])]
        entry = {
            "name": d.name,
            "version": pj.get("version"),
            "tier": m["tier"],
            "status": m["status"],
            "summary": m["summary"],
            "libraries": m.get("libraries", []),
            "dependencies": deps,
            # A bundle ships a copy of other plugins (catalog.yaml ``bundle``) and
            # no content of its own; file mode installs those plugins instead.
            "bundle": bool(m.get("bundle")) and not _has_content(d),
            "bundled": list(m.get("bundle", [])),
        }
        for key in ("replacement", "deprecated_since"):
            if key in m:
                entry[key] = str(m[key])
        entries.append(entry)
    return entries


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
        (assets_dst / "catalog.json").write_text(
            json.dumps({"plugins": entries}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        self.app.display_info(
            f"robotframework-plugins: bundled {', '.join(e['name'] for e in entries)} → {assets_dst} "
            f"({_count_files(assets_dst)} files)"
        )


def _has_content(plugin_dir: Path) -> bool:
    """Ships a skill, a subagent or a hook."""
    return (any((s / "SKILL.md").is_file() for s in (plugin_dir / "skills").glob("*"))
            or any((plugin_dir / "agents").glob("*.md"))
            or (plugin_dir / "hooks" / "hooks.json").is_file())


def _count_files(root: Path) -> int:
    return sum(1 for p in root.rglob("*") if p.is_file())
