"""Upgrading a file-mode install made before the plugin split (spec plugin-split,
"Upgrades from rf-agentskills 3.x keep file-mode installs intact")."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from robotframework_plugins import _assets
from robotframework_plugins.cli import main

PLUGINS = ("rf-core", "rf-web", "rf-api", "rf-mobile", "rf-desktop")
#: Where each agent's project install puts its files.
ROOTS = {"claude-code": ".claude", "codex": ".codex", "cursor": ".cursor", "opencode": ".opencode"}


@pytest.fixture
def old_bundle(tmp_path: Path) -> Path:
    """The pre-split layout: one plugin, rf-agentskills, with all the content."""
    real = Path(str(_assets.bundle_root_traversable()))
    bundle = tmp_path / "old-bundle"
    dst = bundle / "plugins" / "rf-agentskills"
    for name in PLUGINS:
        shutil.copytree(real / "plugins" / name, dst, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("catalog.yaml", "README.md", "CHANGELOG.md", ".claude-plugin"))
    (dst / ".claude-plugin").mkdir()
    (dst / ".claude-plugin" / "plugin.json").write_text('{"name": "rf-agentskills", "version": "3.0.0"}')
    js = dst / "variants" / "opencode" / "plugins" / "rf-core.js"
    js.write_text(js.read_text().replace("rf-core-files", "rf-agentskills-files"))
    js.rename(js.with_name("rf-agentskills.js"))
    (bundle / "catalog.json").write_text(json.dumps({"plugins": [
        {"name": "rf-agentskills", "version": "3.0.0", "tier": "verified", "status": "active",
         "summary": "All of it.", "libraries": []}]}))
    return bundle


def _install(project: Path, agent: str, *extra: str) -> int:
    return main(["install", "--agent", agent, "--scope", "project", "--project", str(project), "--yes", *extra])


def _record(project: Path) -> dict[str, set[str]]:
    data = json.loads((project / ".rf-agentskills" / "installed.json").read_text())
    by_plugin: dict[str, set[str]] = {}
    for ins in data["installations"]:
        for f in ins["files"]:
            by_plugin.setdefault(f["plugin"], set()).add(f["path"])
    return by_plugin


def _skills(project: Path) -> set[str]:
    return {md.parent.name for md in project.rglob("SKILL.md") if "-files" not in md.as_posix()}


def _old_install(project: Path, agent: str, bundle: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with monkeypatch.context() as m:
        m.setattr(_assets, "bundle_root_traversable", lambda: bundle)
        assert _install(project, agent) == 0
    assert (project / ROOTS[agent] / "rf-agentskills-files").is_dir()


@pytest.mark.parametrize("agent", sorted(ROOTS))
def test_file_mode_upgrade(agent: str, old_bundle: Path, fake_home: Path, tmp_path: Path,
                           monkeypatch: pytest.MonkeyPatch) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    _old_install(project, agent, old_bundle, monkeypatch)
    skills_before = _skills(project)
    assert len(skills_before) == 9

    assert _install(project, agent) == 0
    root = project / ROOTS[agent]
    assert _skills(project) == skills_before
    assert set(_record(project)) == set(PLUGINS)
    assert not (root / "rf-agentskills-files").exists()
    assert (root / "rf-core-files" / "scripts").is_dir()
    assert not any((root / f"{p}-files").exists() for p in PLUGINS if p != "rf-core")
    # No hook command, plugin file or config points at the old folder any more.
    for f in root.rglob("*"):
        if f.is_file() and f.suffix in (".json", ".js", ".toml", ".yaml"):
            assert "rf-agentskills-files" not in f.read_text(encoding="utf-8"), f
    if agent == "opencode":
        assert (root / "plugins" / "rf-core.js").is_file() and not (root / "plugins" / "rf-agentskills.js").exists()


def test_claude_code_hooks_are_not_duplicated(old_bundle: Path, fake_home: Path, tmp_path: Path,
                                              monkeypatch: pytest.MonkeyPatch) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    _old_install(project, "claude-code", old_bundle, monkeypatch)
    before = json.loads((project / ".claude" / "settings.json").read_text())["hooks"]
    assert _install(project, "claude-code") == 0
    after = json.loads((project / ".claude" / "settings.json").read_text())["hooks"]
    assert {e: len(g) for e, g in after.items()} == {e: len(g) for e, g in before.items()}
    assert all("rf-core-files" in json.dumps(g) for g in after.values())


def test_narrowing_is_explicit(old_bundle: Path, fake_home: Path, tmp_path: Path,
                               monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    _old_install(project, "claude-code", old_bundle, monkeypatch)
    assert _install(project, "claude-code") == 0
    capsys.readouterr()
    assert _install(project, "claude-code", "--plugins", "rf-core,rf-web") == 0
    assert _skills(project) == {"rf-language", "rf-setup", "rf-python-library", "rf-browser", "rf-selenium"}
    assert set(_record(project)) == {"rf-core", "rf-web"}
    out = " ".join(capsys.readouterr().out.split())
    assert "skills rf-appium, rf-platynui, rf-requests, rf-restinstance" in out
