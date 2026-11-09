"""Pick the plugins a project needs from the libraries it declares.

Reads the project root's ``pyproject.toml`` (PEP 621 ``dependencies`` and
``optional-dependencies``, PEP 735 ``dependency-groups``, Poetry
``dependencies``, ``dev-dependencies`` and ``group.*.dependencies``) and its
``requirements*.txt`` files, and matches the package names against the
``libraries[].package`` of each bundled plugin (spec ``plugin-split``,
"The installer picks plugins from the project").
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib

#: The start of a requirement: the distribution name (PEP 508).
_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def normalize(name: str) -> str:
    """PEP 503 name: lower case, runs of ``-``, ``_`` and ``.`` become ``-``."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement_name(spec: str) -> str | None:
    m = _NAME.match(spec)
    return normalize(m.group(1)) if m else None


def _strings(value: Any) -> list[str]:
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def _pyproject_packages(path: Path) -> set[str]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    specs: list[str] = []
    project = data.get("project", {})
    specs += _strings(project.get("dependencies"))
    for group in (project.get("optional-dependencies") or {}).values():
        specs += _strings(group)
    for group in (data.get("dependency-groups") or {}).values():
        specs += _strings(group)  # include-group tables are skipped
    names = {n for n in map(_requirement_name, specs) if n}
    poetry = data.get("tool", {}).get("poetry", {})
    tables = [poetry.get("dependencies"), poetry.get("dev-dependencies")]
    tables += [g.get("dependencies") for g in (poetry.get("group") or {}).values() if isinstance(g, dict)]
    for table in tables:
        if isinstance(table, dict):
            names |= {normalize(k) for k in table if k.lower() != "python"}
    return names


def _requirements_packages(path: Path) -> set[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return set()
    names = set()
    for line in lines:
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue  # options such as -r, -e, --index-url
        name = _requirement_name(line)
        if name:
            names.add(name)
    return names


def declared_packages(project: Path) -> dict[str, str]:
    """``{normalized package: file that declares it}`` for the project root."""
    found: dict[str, str] = {}
    files = [project / "pyproject.toml", *sorted(project.glob("requirements*.txt"))]
    for f in files:
        if not f.is_file():
            continue
        names = _pyproject_packages(f) if f.name == "pyproject.toml" else _requirements_packages(f)
        for n in sorted(names):
            found.setdefault(n, f.name)
    return found


@dataclass(frozen=True)
class Detection:
    """Plugins chosen for a project, and why."""
    plugins: list[str]
    #: ``{plugin: [(package, declaring file), ...]}`` for the detected plugins.
    reasons: dict[str, list[tuple[str, str]]]

    @property
    def detected(self) -> bool:
        return bool(self.reasons)


def detect(project: Path, catalog: list[dict[str, Any]], core: str = "rf-core") -> Detection:
    """``core`` plus every active verified plugin whose library packages the
    project declares; with no match, every active verified plugin with content.

    Bundles are never chosen: their dependencies are listed instead."""
    candidates = [p for p in catalog
                  if p.get("status") == "active" and p.get("tier") == "verified" and not p.get("bundle")]
    candidates.sort(key=lambda p: p["name"] != core)  # core first: the others depend on it
    declared = declared_packages(project)
    reasons: dict[str, list[tuple[str, str]]] = {}
    for p in candidates:
        for lib in p.get("libraries", []):
            package = normalize(str(lib.get("package", "")))
            if package and package in declared:
                reasons.setdefault(p["name"], []).append((lib["package"], declared[package]))
    if not reasons:
        return Detection(plugins=[p["name"] for p in candidates], reasons={})
    chosen = [p["name"] for p in candidates if p["name"] == core or p["name"] in reasons]
    return Detection(plugins=chosen, reasons=reasons)
