#!/usr/bin/env python3
"""Validate the plugin catalogue and generate what is derived from it.

Every ``plugins/<name>/`` carries a programme manifest, ``catalog.yaml``,
checked against ``schemas/catalog.schema.json`` (spec ``plugin-catalogue``).

    python scripts/build-catalog.py            # validate, then regenerate
    python scripts/build-catalog.py --check    # validate, fail if anything is stale
    python scripts/build-catalog.py --check --base origin/main   # also: renames is append-only
    python scripts/build-catalog.py --version-table   # print the installer release-notes table

A *bundle* is a plugin whose ``catalog.yaml`` lists other plugins under
``bundle`` and that has no content of its own (``rf-agentskills``). The
generator writes ``bundles/<name>/``: real copies of those plugins' skills,
subagents, hooks and hook scripts, plus the bundle's ``plugin.json``, README
and CHANGELOG. The marketplace entry points there. Copies, not plugin
``dependencies``: Claude Code doesn't install dependencies that an update adds,
Copilot CLI and Codex don't install dependencies at all, and Codex drops
symlinks (split-rf-agentskills design D5).

Besides the manifests, the check fails when two listed plugins ship the same
skill, subagent or hook install path, when a plugin contains a symlink, and (with ``--base``) when an existing ``renames``
entry of the marketplace was deleted or changed.

``--root`` points at another tree (tests use scratch copies).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import subprocess
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

    @property
    def dependencies(self) -> list[str]:
        """Names of the plugins this one depends on (``plugin.json``)."""
        deps = self.plugin_json.get("dependencies", [])
        return [d if isinstance(d, str) else d["name"] for d in deps]

    @property
    def bundled(self) -> list[str]:
        """For a bundle, the plugins whose content it ships (``catalog.yaml`` ``bundle``)."""
        return list(self.manifest.get("bundle", []))

    @property
    def has_content(self) -> bool:
        """Ships a skill, a subagent or a hook."""
        return (any((d / "SKILL.md").is_file() for d in (self.path / "skills").glob("*"))
                or any((self.path / "agents").glob("*.md"))
                or (self.path / "hooks" / "hooks.json").is_file())

    @property
    def is_bundle(self) -> bool:
        return bool(self.bundled)


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


# ---------------------------------------------------------------------------
# Cross-plugin checks
# ---------------------------------------------------------------------------

_NAME_LINE = re.compile(r"^name:\s*['\"]?([^'\"\s]+)", re.MULTILINE)


def _frontmatter_name(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    match = _NAME_LINE.search(text[3:end if end > 0 else len(text)])
    return match.group(1) if match else None


def shipped_names(p: Plugin) -> dict[str, set[str]]:
    """What a plugin installs under a name another plugin could also use."""
    skills = {d.name for d in sorted((p.path / "skills").glob("*")) if (d / "SKILL.md").is_file()}
    agents: set[str] = set()
    for f in sorted((p.path / "agents").glob("*.md")):
        agents.add(f.stem)
        name = _frontmatter_name(f)
        if name:
            agents.add(name)
    # Hook scripts install into the plugin's own support folder; the OpenCode
    # JS plugin is the one hook file that lands in a folder shared by plugins.
    hooks = {f"plugins/{f.name}" for f in sorted((p.path / "variants" / "opencode" / "plugins").glob("*"))}
    return {"skill": skills, "subagent": agents, "hook install path": hooks}


def name_problems(plugins: list[Plugin]) -> list[str]:
    owners: dict[tuple[str, str], list[str]] = {}
    for p in listed(plugins):
        for kind, names in shipped_names(p).items():
            for name in names:
                owners.setdefault((kind, name), []).append(p.name)
    return [
        f"{kind} {name!r} is shipped by more than one plugin: {', '.join(sorted(who))}"
        for (kind, name), who in sorted(owners.items()) if len(who) > 1
    ]


def symlink_problems(root: Path, plugins: list[Plugin]) -> list[str]:
    """Plugins contain no symlinks: Codex drops them when it installs a plugin,
    so a shared file is a generated copy instead (launch D15, split D5)."""
    problems = []
    for p in plugins:
        for dirpath, dirnames, filenames in os.walk(p.path):
            for name in sorted(dirnames + filenames):
                link = Path(dirpath) / name
                if link.is_symlink():
                    rel = link.relative_to(root).as_posix()
                    problems.append(f"{rel}: plugins can't contain symlinks ({os.readlink(link)}); "
                                    "Codex drops them, so ship a generated copy")
    return problems


def renames_problems(base: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """The ``renames`` map is append-only: every entry of ``base`` stays as it was."""
    problems = []
    for old, new in base.items():
        if old not in current:
            problems.append(f"marketplace renames: entry {old!r} (-> {new!r}) was deleted; the map is append-only")
        elif current[old] != new:
            problems.append(
                f"marketplace renames: entry {old!r} changed from {new!r} to {current[old]!r}; the map is append-only")
    return problems


def base_renames(root: Path, ref: str) -> dict[str, Any]:
    """``renames`` of the marketplace at git ``ref`` (empty when it has none)."""
    out = subprocess.run(
        ["git", "show", f"{ref}:{MARKETPLACE_REL.as_posix()}"],
        cwd=root, capture_output=True, text=True,
    )
    if out.returncode != 0:
        return {}
    return json.loads(out.stdout).get("renames", {})


# ---------------------------------------------------------------------------
# Generated files
# ---------------------------------------------------------------------------

LISTED = ("active", "deprecated")
README_START = "<!-- catalog:start (generated by scripts/build-catalog.py; do not edit) -->"
README_END = "<!-- catalog:end -->"
MARKETPLACE_REL = Path(".claude-plugin") / "marketplace.json"
BUNDLES_REL = Path("bundles")
#: What a bundle's copies take from each bundled plugin.
BUNDLE_PARTS = ("skills", "agents", "hooks", "scripts")
#: What a bundle's copy takes from the bundle's own folder.
BUNDLE_OWN = (Path(".claude-plugin") / "plugin.json", Path("README.md"), Path("CHANGELOG.md"))
CATALOG_DOC_REL = Path("docs") / "catalog.md"
INSTALLER_PYPROJECT_REL = Path("installer") / "pyproject.toml"
INSTALLER_NAME = "robotframework-plugins"
#: plugin.json fields copied into the marketplace entry when present. Not
#: ``version``: it lives only in plugin.json, which Claude Code reads first.
ENTRY_FIELDS_FROM_PLUGIN_JSON = ("author", "homepage", "repository", "license", "keywords")


def listed(plugins: list[Plugin]) -> list[Plugin]:
    return [p for p in plugins if p.status in LISTED]


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _libraries(p: Plugin) -> str:
    libs = p.manifest["libraries"]
    return ", ".join(lib["name"] for lib in libs) if libs else "Robot Framework"


def _maintainers(p: Plugin) -> str:
    return ", ".join(f"[@{m['github']}](https://github.com/{m['github']})" for m in p.manifest["maintainers"])


def catalog_table(plugins: list[Plugin]) -> str:
    rows = [
        "| Plugin | Version | Tier | Status | What it covers | Libraries | Maintainers |",
        "|---|---|---|---|---|---|---|",
    ]
    for p in listed(plugins):
        status = p.status
        if status == "deprecated":
            status = f"deprecated, use {p.manifest['replacement']}"
        rows.append(
            f"| `{p.name}` | {p.version or '-'} | {p.tier} | {_cell(status)} | {_cell(p.manifest['summary'])} "
            f"| {_cell(_libraries(p))} | {_maintainers(p)} |"
        )
    return "\n".join(rows)


def installer_version(root: Path) -> str:
    path = root / INSTALLER_PYPROJECT_REL
    if not path.is_file():
        raise CatalogError([f"{INSTALLER_PYPROJECT_REL.as_posix()}: missing; the version table needs the installer version"])
    match = re.search(r'^version\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise CatalogError([f"{INSTALLER_PYPROJECT_REL.as_posix()}: no version"])
    return match.group(1)


def version_table(version: str, plugins: list[Plugin]) -> str:
    """What one installer release bundles: active and deprecated plugins."""
    rows = [f"| {INSTALLER_NAME} {version} bundles | Version | Tier |", "|---|---|---|"]
    rows += [f"| `{p.name}` | {p.version or '-'} | {p.tier} |" for p in listed(plugins)]
    return "\n".join(rows)


def readme_block(plugins: list[Plugin], version: str) -> str:
    return (
        f"{README_START}\n"
        f"{catalog_table(plugins)}\n\n"
        "Tiers and what they mean: [GOVERNANCE.md](GOVERNANCE.md). Full details per plugin: "
        f"[docs/catalog.md](docs/catalog.md).\n\n"
        f"The Python installer bundles these plugin versions:\n\n"
        f"{version_table(version, plugins)}\n"
        f"{README_END}"
    )


def render_readme(text: str, plugins: list[Plugin], version: str) -> str:
    start, end = text.find(README_START), text.find(README_END)
    if start < 0 or end < start:
        raise CatalogError([f"README.md: markers {README_START!r} … {README_END!r} not found"])
    return text[:start] + readme_block(plugins, version) + text[end + len(README_END):]


def render_catalog_doc(plugins: list[Plugin], version: str) -> str:
    out = [
        "# Plugin catalogue",
        "",
        "<!-- Generated by scripts/build-catalog.py from plugins/*/catalog.yaml. Do not edit. -->",
        "",
        catalog_table(plugins),
        "",
        "## Installer",
        "",
        f"`pip install {INSTALLER_NAME}=={version}` installs these plugin versions:",
        "",
        version_table(version, plugins),
        "",
    ]
    for p in listed(plugins):
        m = p.manifest
        out += [f"## {p.name}", "", m["summary"], ""]
        out.append(f"- **Tier:** {p.tier}")
        out.append(f"- **Status:** {p.status}")
        if p.status == "deprecated":
            out.append(f"- **Deprecated since:** {m['deprecated_since']}; **use instead:** {m['replacement']}")
        out.append(f"- **Version:** {p.version or '-'}")
        out.append(f"- **Robot Framework:** `{m['robotframework']}`")
        if m["libraries"]:
            out.append("- **Libraries:**")
            out += [f"  - {lib['name']} (`{lib['package']}` `{lib['versions']}`)" for lib in m["libraries"]]
        out.append(f"- **Tested with:** {', '.join(m['agents'])}")
        out.append(f"- **Maintainers:** {_maintainers(p)}")
        out.append(f"- **Install (Claude Code):** `/plugin install {p.name}@robotframework-plugins`")
        out.append("")
    return "\n".join(out)


def marketplace_entry(p: Plugin) -> dict[str, Any]:
    source = f"./{BUNDLES_REL.as_posix()}/{p.name}" if p.is_bundle else f"./plugins/{p.name}"
    entry: dict[str, Any] = {
        "name": p.name,
        "source": source,
        "description": p.manifest["summary"],
    }
    for key in ENTRY_FIELDS_FROM_PLUGIN_JSON:
        if key in p.plugin_json:
            entry[key] = p.plugin_json[key]
    entry["category"] = "testing"
    tags = ["robot-framework", p.tier]
    if p.status == "deprecated":
        tags.append("deprecated")
    entry["tags"] = tags
    return entry


def render_marketplace(current: dict[str, Any], plugins: list[Plugin]) -> dict[str, Any]:
    """``current`` with its ``plugins`` list regenerated; other top-level keys kept.

    A ``removed`` plugin's name is appended to ``renames`` as ``null``; existing
    entries (hand-written ``"<old>": "<new>"`` renames too) stay. Claude Code
    uninstalls plugins that leave the marketplace (``forceRemoveDeletedPlugins``).
    """
    out = dict(current)
    metadata = {k: v for k, v in out.get("metadata", {}).items() if k != "version"}
    if metadata:
        out["metadata"] = metadata
    else:
        out.pop("metadata", None)
    out["plugins"] = [marketplace_entry(p) for p in listed(plugins)]
    renames = dict(out.get("renames", {}))
    for p in plugins:
        if p.status == "removed":
            renames.setdefault(p.name, None)
    if renames:
        out["renames"] = renames
    out["forceRemoveDeletedPlugins"] = True
    return out


def _dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def bundle_problems(plugins: list[Plugin]) -> list[str]:
    """A listed plugin needs content, or must be a bundle of listed plugins
    that has none of its own; dependencies name listed plugins."""
    by_name = {p.name: p for p in plugins}
    problems = []
    for p in listed(plugins):
        rel = f"plugins/{p.name}"
        if p.is_bundle:
            if p.has_content:
                problems.append(f"{rel}: a bundle ships no content of its own; its copy is generated "
                                f"into {BUNDLES_REL.as_posix()}/{p.name}/")
            if p.dependencies:
                problems.append(f"{rel}/.claude-plugin/plugin.json: a bundle declares no dependencies "
                                "(it ships a copy instead)")
            for name in p.bundled:
                if name not in by_name or by_name[name].status not in LISTED or by_name[name].is_bundle:
                    problems.append(f"{rel}/catalog.yaml: bundle: {name!r} is not a listed plugin with content")
        elif not p.has_content:
            problems.append(f"{rel}: ships no skill, subagent or hook; a plugin needs content")
        for dep in p.dependencies:
            if dep not in by_name or by_name[dep].status not in LISTED:
                problems.append(f"{rel}/.claude-plugin/plugin.json: dependency {dep!r} is not a listed plugin")
    return problems


def _bundle_files(dep: Plugin) -> list[Path]:
    return sorted(f for part in BUNDLE_PARTS for f in (dep.path / part).rglob("*")
                  if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc")


def bundle_copies(root: Path, bundle: Plugin, plugins: list[Plugin]) -> dict[Path, str]:
    """``bundles/<name>/``: the bundled plugins' content, plus the bundle's
    own ``plugin.json``, README and CHANGELOG."""
    by_name = {p.name: p for p in plugins}
    out_dir = root / BUNDLES_REL / bundle.name
    files: dict[Path, str] = {}
    origin: dict[Path, str] = {}
    for name in bundle.bundled:
        for f in _bundle_files(by_name[name]):
            dst = out_dir / f.relative_to(by_name[name].path)
            if dst in files:
                raise CatalogError([f"bundles/{bundle.name}: {dst.relative_to(out_dir).as_posix()} "
                                    f"is shipped by both {origin[dst]} and {name}"])
            files[dst] = f.read_text(encoding="utf-8")
            origin[dst] = name
    for rel in BUNDLE_OWN:
        if (bundle.path / rel).is_file():
            files[out_dir / rel] = (bundle.path / rel).read_text(encoding="utf-8")
    return files


def generated_files(root: Path, plugins: list[Plugin]) -> dict[Path, str]:
    """Every generated file and the content it should have."""
    readme = root / "README.md"
    market = root / MARKETPLACE_REL
    version = installer_version(root)
    current = json.loads(market.read_text(encoding="utf-8"))
    files = {
        readme: render_readme(readme.read_text(encoding="utf-8"), plugins, version),
        root / CATALOG_DOC_REL: render_catalog_doc(plugins, version),
        market: _dump_json(render_marketplace(current, plugins)),
    }
    for p in listed(plugins):
        if p.is_bundle:
            files.update(bundle_copies(root, p, plugins))
    return files


def stray_files(root: Path, files: dict[Path, str]) -> list[Path]:
    """Files under ``bundles/`` that the generator no longer writes."""
    bundles = root / BUNDLES_REL
    if not bundles.is_dir():
        return []
    return sorted(f for f in bundles.rglob("*") if f.is_file() and f not in files)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="validate and fail on stale generated files")
    ap.add_argument("--root", type=Path, default=REPO, help="repository root (default: this checkout)")
    ap.add_argument("--base", help="git ref (the PR base) whose marketplace renames must all be kept")
    ap.add_argument("--version-table", action="store_true",
                    help="print the table of bundled plugin versions (installer release notes) and exit")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    try:
        plugins = load_plugins(root)
        if args.version_table:
            print(version_table(installer_version(root), plugins))
            return 0
        problems = name_problems(plugins) + symlink_problems(root, plugins) + bundle_problems(plugins)
        market = json.loads((root / MARKETPLACE_REL).read_text(encoding="utf-8"))
        if args.base:
            problems += renames_problems(base_renames(root, args.base), market.get("renames", {}))
        if problems:
            raise CatalogError(problems)
        files = generated_files(root, plugins)
    except CatalogError as exc:
        for p in exc.problems:
            print(f"error: {p}", file=sys.stderr)
        return 1
    stale = [path for path, text in files.items()
             if not path.is_file() or path.read_text(encoding="utf-8") != text]
    stray = stray_files(root, files)
    if args.check:
        for path in stale:
            print(f"error: {path.relative_to(root)} is out of date", file=sys.stderr)
        for path in stray:
            print(f"error: {path.relative_to(root)} is not generated any more", file=sys.stderr)
        if stale or stray:
            print("Regenerate with: python scripts/build-catalog.py", file=sys.stderr)
            return 1
        print(f"catalogue: {len(plugins)} plugin(s) valid, generated files up to date")
        return 0
    for path in stale:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(files[path], encoding="utf-8")
        print(f"wrote {path.relative_to(root)}")
    for path in stray:
        path.unlink()
        print(f"removed {path.relative_to(root)}")
    print(f"catalogue: {len(plugins)} plugin(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
