#!/usr/bin/env python3
"""Choose which plugins' tests a change must run (spec ``plugin-catalogue``).

The shared tests in ``tests/`` always run. A plugin's own tests
(``plugins/<name>/tests/``) run when:

* a file under ``plugins/<name>/`` changed, or
* a file that one of the plugin's symlinks points to changed (a shared file
  lives in one plugin and the others link to it), or
* a plugin it depends on, or one that depends on it, was selected by the two
  rules above (``rf-core``'s tests check the routes to technology skills, and a
  technology plugin's tests may read ``rf-core``), or
* a file outside ``plugins/`` changed (shared scripts, the installer, the
  workflows): those can affect every plugin, so every plugin runs, or
* no list of changed paths is given (push to main, release): every plugin runs.

    python scripts/select-plugin-tests.py --base origin/main
    python scripts/select-plugin-tests.py --paths-file changed.txt --github-output "$GITHUB_OUTPUT"

Prints one plugin name per line. ``--github-output`` also appends
``plugins=<JSON list>``.

``--security`` chooses the plugins the security gate scans instead
(content-security-scanning; plugin-catalogue "Shared files have one owner"):
every plugin with shipped content (skills, subagents, hooks or scripts) and
every bundle. A plugin is scanned when a file under ``plugins/<name>/``
changed; a bundle when its own folder, its generated copy under
``bundles/<name>/`` or one of its member plugins changed, since the bundle
carries copies of their files. A change outside ``plugins/`` and ``bundles/``
(the scanners, baselines, workflows) scans everything.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[1]


def plugins_with_tests(root: Path) -> list[str]:
    return sorted(p.parent.name for p in (root / "plugins").glob("*/tests") if p.is_dir())


def _links_into(root: Path, plugin: str) -> set[str]:
    """Repository paths (POSIX, relative) that the plugin's symlinks point to."""
    targets: set[str] = set()
    base = root / "plugins" / plugin
    for dirpath, dirnames, filenames in os.walk(base):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            if path.is_symlink():
                target = path.resolve()
                try:
                    targets.add(target.relative_to(root.resolve()).as_posix())
                except ValueError:
                    continue  # leaves the repository; the catalogue check rejects it
    return targets


def dependencies(root: Path) -> dict[str, set[str]]:
    """``{plugin: names of the plugins in its plugin.json dependencies}``."""
    deps: dict[str, set[str]] = {}
    for pj in sorted((root / "plugins").glob("*/.claude-plugin/plugin.json")):
        data = json.loads(pj.read_text(encoding="utf-8"))
        deps[pj.parent.parent.name] = {d if isinstance(d, str) else d["name"]
                                       for d in data.get("dependencies", [])}
    return deps


def _with_neighbours(root: Path, selected: set[str]) -> set[str]:
    deps = dependencies(root)
    out = set(selected)
    for name in selected:
        out |= deps.get(name, set())
        out |= {other for other, theirs in deps.items() if name in theirs}
    return out


def select(root: Path, changed: list[str] | None) -> list[str]:
    plugins = plugins_with_tests(root)
    if changed is None:
        return plugins
    selected: set[str] = set()
    links = {p: _links_into(root, p) for p in plugins}
    for raw in changed:
        parts = PurePosixPath(raw.strip()).parts
        if not parts:
            continue
        if parts[0] != "plugins":
            return plugins
        if len(parts) > 1 and (root / "plugins" / parts[1]).is_dir():
            # Even a plugin without tests of its own: its neighbours' tests run.
            selected.add(parts[1])
        path = "/".join(parts)
        for plugin, targets in links.items():
            if any(path == t or path.startswith(t + "/") for t in targets):
                selected.add(plugin)
    return sorted(_with_neighbours(root, selected) & set(plugins))


CONTENT_DIRS = ("skills", "agents", "hooks", "scripts")


def bundles(root: Path) -> dict[str, set[str]]:
    """``{bundle: its member plugins}`` from each ``catalog.yaml`` ``bundle:`` list."""
    import yaml

    out: dict[str, set[str]] = {}
    for cat in sorted((root / "plugins").glob("*/catalog.yaml")):
        data = yaml.safe_load(cat.read_text(encoding="utf-8")) or {}
        if data.get("bundle"):
            out[cat.parent.name] = set(data["bundle"])
    return out


def content_plugins(root: Path) -> list[str]:
    return sorted(p.name for p in (root / "plugins").iterdir()
                  if p.is_dir() and any((p / d).is_dir() for d in CONTENT_DIRS))


def select_security(root: Path, changed: list[str] | None) -> list[str]:
    members = bundles(root)
    every = sorted(set(content_plugins(root)) | set(members))
    if changed is None:
        return every
    selected: set[str] = set()
    for raw in changed:
        parts = PurePosixPath(raw.strip()).parts
        if not parts:
            continue
        if parts[0] not in ("plugins", "bundles"):
            return every
        if len(parts) > 1 and parts[1] in every:
            selected.add(parts[1])
    selected |= {b for b, m in members.items() if m & selected}
    return sorted(selected & set(every))


def _changed_paths(root: Path, base: str | None, paths_file: Path | None) -> list[str] | None:
    if paths_file is not None:
        return [ln for ln in paths_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if base is None:
        return None
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=root, capture_output=True, text=True, check=True,
    )
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--base", help="git ref to diff against (the PR base)")
    group.add_argument("--paths-file", type=Path, help="changed paths, one per line")
    parser.add_argument("--github-output", type=Path, help="append plugins=<JSON list> here")
    parser.add_argument("--security", action="store_true", help="choose the plugins the security gate scans")
    parser.add_argument("--root", type=Path, default=REPO, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    chooser = select_security if args.security else select
    selected = chooser(args.root, _changed_paths(args.root, args.base, args.paths_file))
    for name in selected:
        print(name)
    if args.github_output is not None:
        with args.github_output.open("a", encoding="utf-8") as fh:
            fh.write(f"plugins={json.dumps(selected)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
