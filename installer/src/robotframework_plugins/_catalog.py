"""Build catalogue entries from plugin folders.

Shared by the wheel's build hook (``hatch_build.py`` loads this file by path,
because the package isn't importable at build time) and by ``bundle.fetch()``,
which builds the catalogue of a downloaded repository snapshot. Both must
produce the same entries, so the rules live here once.

Only the standard library and PyYAML (a package dependency) are used.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

#: Version of the catalogue's shape (``catalog.json`` ``format``). Bumped only
#: on a breaking change to the documented entry fields; see the README's
#: "Python API" section.
CATALOG_FORMAT = 1
#: Statuses that are bundled; ``removed`` plugins stay out.
BUNDLED_STATUSES = ("active", "deprecated")
#: A plugin's own top-level folders that are for this repository's CI, not for
#: users. Skills ship example ``tests/`` folders too, so only the plugin root.
PLUGIN_ONLY_DIRS = frozenset({"tests", "evals"})
_REQUIRED_MANIFEST = ("tier", "status", "summary")


class CatalogError(ValueError):
    """A plugin folder whose manifest can't be turned into a catalogue entry."""


def has_content(plugin_dir: Path) -> bool:
    """Ships a skill, a subagent or a hook."""
    return (any((s / "SKILL.md").is_file() for s in (plugin_dir / "skills").glob("*"))
            or any((plugin_dir / "agents").glob("*.md"))
            or (plugin_dir / "hooks" / "hooks.json").is_file())


def _manifest(plugin_dir: Path) -> dict[str, Any]:
    path = plugin_dir / "catalog.yaml"
    if not path.is_file():
        raise CatalogError(f"{plugin_dir.name}: catalog.yaml missing; run scripts/build-catalog.py --check")
    try:
        m = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CatalogError(f"{plugin_dir.name}: catalog.yaml is not valid YAML ({exc})") from exc
    if not isinstance(m, dict):
        raise CatalogError(f"{plugin_dir.name}: catalog.yaml is not a mapping")
    missing = [k for k in _REQUIRED_MANIFEST if not m.get(k)]
    if missing:
        raise CatalogError(f"{plugin_dir.name}: catalog.yaml lacks {', '.join(missing)}")
    return m


def _plugin_json(plugin_dir: Path) -> dict[str, Any]:
    path = plugin_dir / ".claude-plugin" / "plugin.json"
    if not path.is_file():
        raise CatalogError(f"{plugin_dir.name}: .claude-plugin/plugin.json missing")
    try:
        pj = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CatalogError(f"{plugin_dir.name}: plugin.json is not valid JSON ({exc})") from exc
    if not isinstance(pj, dict) or not pj.get("version"):
        raise CatalogError(f"{plugin_dir.name}: plugin.json lacks version")
    return pj


def catalog_entries(plugins_dir: Path) -> list[dict[str, Any]]:
    """One entry per bundled plugin under ``plugins_dir``, from its catalog.yaml and plugin.json."""
    entries = []
    for d in sorted(p for p in plugins_dir.iterdir() if p.is_dir()):
        m = _manifest(d)
        if m["status"] not in BUNDLED_STATUSES:
            continue
        pj = _plugin_json(d)
        deps = [x if isinstance(x, str) else x["name"] for x in pj.get("dependencies", [])]
        entry = {
            "name": d.name,
            "version": pj.get("version"),
            "tier": m["tier"],
            "status": m["status"],
            "summary": m["summary"],
            "libraries": m.get("libraries", []),
            "robotframework": str(m.get("robotframework", "")),
            "dependencies": deps,
            # A bundle ships a copy of other plugins (catalog.yaml ``bundle``) and
            # no content of its own; file mode installs those plugins instead.
            "bundle": bool(m.get("bundle")) and not has_content(d),
            "bundled": list(m.get("bundle", [])),
        }
        for key in ("replacement", "deprecated_since"):
            if key in m:
                entry[key] = str(m[key])
        entries.append(entry)
    return entries


def catalog_document(entries: list[dict[str, Any]]) -> str:
    """The ``catalog.json`` text for ``entries``."""
    return json.dumps({"format": CATALOG_FORMAT, "plugins": entries}, indent=2, ensure_ascii=False) + "\n"


#: The plugin listed first by ``skills_dirs()``: the others depend on it.
CORE_PLUGIN = "rf-core"


def skill_dirs(entries: list[dict[str, Any]], root: Path) -> dict[str, Path]:
    """``{name: <root>/plugins/<name>/skills}`` for every active plugin in ``entries``
    that isn't a bundle and has at least one ``*/SKILL.md``; ``rf-core`` first,
    then catalogue order."""
    names = [e["name"] for e in entries if e.get("status") == "active" and not e.get("bundle")]
    if CORE_PLUGIN in names:
        names.remove(CORE_PLUGIN)
        names.insert(0, CORE_PLUGIN)
    out: dict[str, Path] = {}
    for name in names:
        skills = root / "plugins" / name / "skills"
        if any(skills.glob("*/SKILL.md")):
            out[name] = skills.resolve()
    return out
