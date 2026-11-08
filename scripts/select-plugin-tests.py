#!/usr/bin/env python3
"""Choose which plugins' tests a change must run (spec ``plugin-catalogue``).

The shared tests in ``tests/`` always run. A plugin's own tests
(``plugins/<name>/tests/``) run when:

* a file under ``plugins/<name>/`` changed, or
* a file that one of the plugin's symlinks points to changed (a shared file
  lives in one plugin and the others link to it), or
* a file outside ``plugins/`` changed (shared scripts, the installer, the
  workflows): those can affect every plugin, so every plugin runs, or
* no list of changed paths is given (push to main, release): every plugin runs.

    python scripts/select-plugin-tests.py --base origin/main
    python scripts/select-plugin-tests.py --paths-file changed.txt --github-output "$GITHUB_OUTPUT"

Prints one plugin name per line. ``--github-output`` also appends
``plugins=<JSON list>``.
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
        if len(parts) > 1 and parts[1] in links:
            selected.add(parts[1])
        path = "/".join(parts)
        for plugin, targets in links.items():
            if any(path == t or path.startswith(t + "/") for t in targets):
                selected.add(plugin)
    return sorted(selected)


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
    parser.add_argument("--root", type=Path, default=REPO, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    selected = select(args.root, _changed_paths(args.root, args.base, args.paths_file))
    for name in selected:
        print(name)
    if args.github_output is not None:
        with args.github_output.open("a", encoding="utf-8") as fh:
            fh.write(f"plugins={json.dumps(selected)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
