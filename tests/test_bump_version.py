"""scripts/bump-version.sh bumps the one release version (spec release-train)."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from _shell import BASH, requires_posix_bash

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "bump-version.sh"


def _scratch(tmp_path: Path, version: str) -> Path:
    """The files bump-version.sh and build-catalog.py read and write."""
    repo = tmp_path / "repo"

    def ignore(directory: str, names: list[str]) -> set[str]:
        top = Path(directory).parent == ROOT / "plugins"
        return {n for n in names if n == "__pycache__" or (top and n in ("variants", "tests", "evals"))}

    shutil.copytree(ROOT / "plugins", repo / "plugins", ignore=ignore)
    for rel in ("scripts/bump-version.sh", "scripts/build-catalog.py", "schemas/catalog.schema.json",
                ".claude-plugin/marketplace.json", "README.md", "docs/catalog.md", "installer/pyproject.toml",
                "installer/src/robotframework_plugins/__init__.py", "uv.lock"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, repo / rel)
    pyproject = repo / "installer" / "pyproject.toml"
    pyproject.write_text(re.sub(r'^version = "[^"]*"', f'version = "{version}"', pyproject.read_text(encoding="utf-8"),
                                count=1, flags=re.M), encoding="utf-8")
    (repo / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n\n### rf-web\n- A change.\n", encoding="utf-8")
    return repo


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {"REPO_ROOT": str(repo), "PATH": os.pathsep.join([str(Path(sys.executable).parent), "/usr/bin", "/bin"])}
    return subprocess.run([BASH, str(repo / "scripts" / "bump-version.sh"), *args],
                          capture_output=True, text=True, env=env)


def _versions(repo: Path) -> set[str]:
    return {json.loads(pj.read_text(encoding="utf-8"))["version"]
            for pj in (repo / "plugins").glob("*/.claude-plugin/plugin.json")}


@requires_posix_bash
@pytest.mark.parametrize(("start", "args", "release", "plugins"), [
    ("5.0.0", ("minor",), "5.1.0", "5.1.0"),
    ("5.0.0", ("major",), "6.0.0", "6.0.0"),
    ("5.0.0", ("patch",), "5.0.1", "5.0.1"),
    ("5.0.0", ("--rc", "minor"), "5.1.0rc1", "5.1.0-rc.1"),
    ("5.1.0rc1", ("--rc", "minor"), "5.1.0rc2", "5.1.0-rc.2"),
    ("5.1.0rc1", ("patch",), "5.1.0", "5.1.0"),
])
def test_bump_sets_every_copy(tmp_path: Path, start: str, args: tuple[str, ...], release: str, plugins: str) -> None:
    repo = _scratch(tmp_path, start)
    skills_before = {md: md.read_bytes() for md in (repo / "plugins").glob("*/skills/*/SKILL.md")}
    res = _run(repo, *args)
    assert res.returncode == 0, res.stdout + res.stderr
    assert f'version = "{release}"' in (repo / "installer" / "pyproject.toml").read_text(encoding="utf-8")
    assert f'__version__ = "{release}"' in (repo / "installer/src/robotframework_plugins/__init__.py").read_text(
        encoding="utf-8")
    assert f'name = "robotframework-plugins"\nversion = "{release}"' in (repo / "uv.lock").read_text(encoding="utf-8")
    assert _versions(repo) == {plugins}
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert re.search(rf"^## Unreleased\n\n## {re.escape(release)} — \d{{4}}-\d{{2}}-\d{{2}}\n\n### rf-web", changelog, re.M)
    assert f"v{release}" in res.stdout
    assert {md: md.read_bytes() for md in skills_before} == skills_before


@requires_posix_bash
def test_old_plugin_form_is_refused(tmp_path: Path) -> None:
    repo = _scratch(tmp_path, "5.0.0")
    before = _versions(repo)
    res = _run(repo, "rf-core", "minor")
    assert res.returncode != 0 and "Usage" in res.stderr
    assert _versions(repo) == before
