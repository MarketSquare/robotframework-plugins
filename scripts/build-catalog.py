#!/usr/bin/env python3
"""Validate the plugin catalogue and generate what is derived from it.

Every ``plugins/<name>/`` carries a programme manifest, ``catalog.yaml``,
checked against ``schemas/catalog.schema.json`` (spec ``plugin-catalogue``).

    python scripts/build-catalog.py            # validate, then regenerate
    python scripts/build-catalog.py --check    # validate, fail if anything is stale

``--root`` points at another tree (tests use scratch copies).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[1]
SCHEMA_REL = Path("schemas") / "catalog.schema.json"
MANIFEST = "catalog.yaml"


class CatalogError(Exception):
    """One or more catalogue problems; ``problems`` lists them."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("\n".join(problems))
        self.problems = problems


@dataclass
class Plugin:
    name: str
    path: Path
    manifest: dict[str, Any]
    plugin_json: dict[str, Any] = field(default_factory=dict)

    @property
    def version(self) -> str | None:
        return self.plugin_json.get("version")

    @property
    def status(self) -> str:
        return self.manifest["status"]

    @property
    def tier(self) -> str:
        return self.manifest["tier"]


def _load_yaml(path: Path) -> Any:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _dates_to_str(data)


def _dates_to_str(value: Any) -> Any:
    """YAML turns unquoted dates into ``date`` objects; the schema wants strings."""
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _dates_to_str(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_dates_to_str(v) for v in value]
    return value


def schema(root: Path = REPO) -> dict[str, Any]:
    return json.loads((root / SCHEMA_REL).read_text(encoding="utf-8"))


def validate_manifest(data: Any, where: str, root: Path = REPO) -> list[str]:
    """Schema problems of one manifest, as ``<where>: <field>: <message>`` lines."""
    validator = Draft202012Validator(schema(root))
    problems = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(p) for p in err.absolute_path) or "(top level)"
        problems.append(f"{where}: {loc}: {err.message}")
    return problems


def load_plugins(root: Path = REPO) -> list[Plugin]:
    """Every plugin under ``plugins/``, validated. Raises :class:`CatalogError`."""
    problems: list[str] = []
    plugins: list[Plugin] = []
    plugins_dir = root / "plugins"
    for d in sorted(p for p in plugins_dir.iterdir() if p.is_dir()):
        rel = d.relative_to(root).as_posix()
        manifest_path = d / MANIFEST
        if not manifest_path.is_file():
            problems.append(f"{rel}/{MANIFEST}: missing; every plugin needs a programme manifest")
            continue
        data = _load_yaml(manifest_path)
        found = validate_manifest(data, f"{rel}/{MANIFEST}", root)
        problems.extend(found)
        if found:
            continue
        if data["name"] != d.name:
            problems.append(f"{rel}/{MANIFEST}: name: {data['name']!r} differs from the directory name {d.name!r}")
        pj_path = d / ".claude-plugin" / "plugin.json"
        pj: dict[str, Any] = {}
        if data["status"] != "removed":
            if not pj_path.is_file():
                problems.append(f"{rel}/.claude-plugin/plugin.json: missing")
            else:
                pj = json.loads(pj_path.read_text(encoding="utf-8"))
                if pj.get("name") != d.name:
                    problems.append(
                        f"{rel}/.claude-plugin/plugin.json: name: {pj.get('name')!r} differs from {d.name!r}")
        plugins.append(Plugin(name=d.name, path=d, manifest=data, plugin_json=pj))
    if problems:
        raise CatalogError(problems)
    return plugins


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="validate and fail on stale generated files")
    ap.add_argument("--root", type=Path, default=REPO, help="repository root (default: this checkout)")
    args = ap.parse_args(argv)
    try:
        plugins = load_plugins(args.root)
    except CatalogError as exc:
        for p in exc.problems:
            print(f"error: {p}", file=sys.stderr)
        return 1
    print(f"catalogue: {len(plugins)} plugin(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
