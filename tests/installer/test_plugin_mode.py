"""``robotframework-plugins install --mode plugin`` (marketplace-distribution, installer-plugin-bootstrap).

Plugin mode points agents at the robotframework-plugins marketplace instead
of copying files: committed ``.claude/settings.json`` entries for Claude Code,
Copilot (also ``.github/copilot/settings.json``), VS Code and Cursor; Codex gets
its TOML subagents plus the per-user ``codex plugin`` commands.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from robotframework_plugins import transforms as _x
from robotframework_plugins.cli import main

MARKETPLACE = "robotframework-plugins"
PLUGIN_ID = "rf-agentskills@robotframework-plugins"


@pytest.fixture(autouse=True)
def _force_node(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_x, "node_available", lambda: True)


def _install(project: Path, *extra: str) -> int:
    return main(["install", "--scope", "project", "--project", str(project), *extra])


def _settings(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_plugin_mode_writes_marketplace_settings_and_no_files(tmp_path: Path, fake_home: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    assert _install(project, "--agent", "claude-code", "--mode", "plugin") == 0
    data = _settings(project / ".claude" / "settings.json")
    assert data["extraKnownMarketplaces"][MARKETPLACE]["source"] == {
        "source": "github", "repo": "MarketSquare/robotframework-plugins"}
    assert data["enabledPlugins"] == {PLUGIN_ID: True}
    assert not (project / ".claude" / "skills").exists()
    assert not (project / ".claude" / "agents").exists()


def test_existing_settings_survive_and_uninstall_removes_only_our_entries(
    tmp_path: Path, fake_home: Path
) -> None:
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    settings = project / ".claude" / "settings.json"
    foreign = {
        "model": "opus",
        "hooks": {"Notification": [{"matcher": "*", "hooks": [{"type": "command", "command": "echo hi"}]}]},
        "enabledPlugins": {"other@mkt": True},
        "extraKnownMarketplaces": {"mkt": {"source": {"source": "github", "repo": "o/r"}}},
    }
    settings.write_text(json.dumps(foreign), encoding="utf-8")
    assert _install(project, "--agent", "claude-code", "--mode", "plugin") == 0
    data = _settings(settings)
    assert data["model"] == "opus" and data["hooks"] == foreign["hooks"]
    assert data["enabledPlugins"] == {"other@mkt": True, PLUGIN_ID: True}
    assert set(data["extraKnownMarketplaces"]) == {"mkt", MARKETPLACE}
    assert main(["uninstall", "--agent", "claude-code", "--scope", "project", "--project", str(project)]) == 0
    assert _settings(settings) == foreign


def test_ref_pins_the_marketplace(tmp_path: Path, fake_home: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    assert _install(project, "--agent", "claude-code", "--mode", "plugin", "--ref", "v2.1.0") == 0
    source = _settings(project / ".claude" / "settings.json")["extraKnownMarketplaces"][MARKETPLACE]["source"]
    assert source["ref"] == "v2.1.0"


def test_ref_without_plugin_mode_is_rejected(tmp_path: Path, fake_home: Path) -> None:
    assert _install(tmp_path, "--agent", "claude-code", "--ref", "v2.1.0") == 2


def test_copilot_also_writes_its_own_settings(tmp_path: Path, fake_home: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    assert _install(project, "--agent", "copilot", "--mode", "plugin") == 0
    for path in (project / ".claude" / "settings.json", project / ".github" / "copilot" / "settings.json"):
        data = _settings(path)
        assert data["enabledPlugins"] == {PLUGIN_ID: True}, path
        assert MARKETPLACE in data["extraKnownMarketplaces"], path


def test_switching_from_files_to_plugin_removes_copies_and_old_hooks(tmp_path: Path, fake_home: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    assert _install(project, "--agent", "claude-code") == 0
    assert (project / ".claude" / "skills" / "rf-python-library" / "SKILL.md").is_file()
    assert "hooks" in _settings(project / ".claude" / "settings.json")
    assert _install(project, "--agent", "claude-code", "--mode", "plugin") == 0
    assert not (project / ".claude" / "skills" / "rf-python-library" / "SKILL.md").exists()
    data = _settings(project / ".claude" / "settings.json")
    assert not data.get("hooks") and data["enabledPlugins"] == {PLUGIN_ID: True}


def test_codex_plugin_mode_installs_agents_and_prints_commands(
    tmp_path: Path, fake_home: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess
    calls: list[list[str]] = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: calls.append(cmd))  # must not run
    project = tmp_path / "proj"
    project.mkdir()
    assert _install(project, "--agent", "codex", "--mode", "plugin", "--ref", "v2.1.0") == 0
    agents = sorted(p.name for p in (project / ".codex" / "agents").glob("*.toml"))
    assert len(agents) == 3 and "rf-debug-expert.toml" in agents
    out = " ".join(capsys.readouterr().out.split())
    assert "codex plugin marketplace add MarketSquare/robotframework-plugins --ref v2.1.0" in out
    assert f"codex plugin add {PLUGIN_ID}" in out and "/hooks" in out
    assert calls == []
    assert not (project / ".codex" / "skills").exists()


def test_codex_plugin_mode_runs_commands_with_yes(
    tmp_path: Path, fake_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import shutil
    import subprocess
    calls: list[list[str]] = []

    class _Done:
        returncode = 0

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: calls.append(cmd) or _Done())
    project = tmp_path / "proj"
    project.mkdir()
    assert _install(project, "--agent", "codex", "--mode", "plugin", "--yes") == 0
    assert calls == [
        ["codex", "plugin", "marketplace", "add", "MarketSquare/robotframework-plugins"],
        ["codex", "plugin", "add", PLUGIN_ID],
    ]


def test_cursor_plugin_mode_prints_steps_only(
    tmp_path: Path, fake_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    assert _install(project, "--agent", "cursor", "--mode", "plugin") == 0
    out = " ".join(capsys.readouterr().out.split())
    assert "https://github.com/MarketSquare/robotframework-plugins" in out
    assert not (project / ".cursor").exists()


@pytest.mark.parametrize("agent", ["opencode", "goose"])
def test_agents_without_marketplace_fall_back_to_files(
    tmp_path: Path, fake_home: Path, capsys: pytest.CaptureFixture[str], agent: str
) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    assert _install(project, "--agent", agent, "--mode", "plugin") == 0
    assert "installing files instead" in " ".join(capsys.readouterr().out.split())
    assert list(project.rglob("SKILL.md")) or list(fake_home.rglob("SKILL.md"))


OLD_MARKETPLACE = "robotframework-agentskills"
OLD_PLUGIN_ID = "rf-agentskills@robotframework-agentskills"


def _old_settings(ref: str | None = None) -> dict:
    source = {"source": "github", "repo": "manykarim/robotframework-agentskills"}
    if ref:
        source["ref"] = ref
    return {
        "model": "opus",
        "extraKnownMarketplaces": {OLD_MARKETPLACE: {"source": source}, "mkt": {"source": {"source": "github", "repo": "o/r"}}},
        "enabledPlugins": {OLD_PLUGIN_ID: True, "other@mkt": True},
    }


def test_old_marketplace_entry_migrated(
    tmp_path: Path, fake_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    settings = project / ".claude" / "settings.json"
    settings.write_text(json.dumps(_old_settings()), encoding="utf-8")
    assert _install(project, "--agent", "claude-code", "--mode", "plugin", "--yes") == 0
    data = _settings(settings)
    assert data["model"] == "opus"
    assert set(data["extraKnownMarketplaces"]) == {"mkt", MARKETPLACE}
    assert data["enabledPlugins"] == {"other@mkt": True, PLUGIN_ID: True}
    out = " ".join(capsys.readouterr().out.split())
    assert "replaced the robotframework-agentskills marketplace" in out


def test_old_marketplace_ref_pin_is_kept(tmp_path: Path, fake_home: Path) -> None:
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    settings = project / ".claude" / "settings.json"
    settings.write_text(json.dumps(_old_settings(ref="v3.0.0")), encoding="utf-8")
    assert _install(project, "--agent", "claude-code", "--mode", "plugin", "--yes") == 0
    assert _settings(settings)["extraKnownMarketplaces"][MARKETPLACE]["source"]["ref"] == "v3.0.0"


def test_new_ref_overrides_old_pin(tmp_path: Path, fake_home: Path) -> None:
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    settings = project / ".claude" / "settings.json"
    settings.write_text(json.dumps(_old_settings(ref="v3.0.0")), encoding="utf-8")
    assert _install(project, "--agent", "claude-code", "--mode", "plugin", "--yes", "--ref", "rf-agentskills--v3.1.0") == 0
    assert _settings(settings)["extraKnownMarketplaces"][MARKETPLACE]["source"]["ref"] == "rf-agentskills--v3.1.0"


def test_same_named_foreign_marketplace_is_not_migrated(tmp_path: Path, fake_home: Path) -> None:
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    settings = project / ".claude" / "settings.json"
    foreign = {"extraKnownMarketplaces": {OLD_MARKETPLACE: {"source": {"source": "github", "repo": "someone/fork"}}}}
    settings.write_text(json.dumps(foreign), encoding="utf-8")
    assert _install(project, "--agent", "claude-code", "--mode", "plugin", "--yes") == 0
    assert OLD_MARKETPLACE in _settings(settings)["extraKnownMarketplaces"]


def test_copilot_settings_migrated_too(tmp_path: Path, fake_home: Path) -> None:
    project = tmp_path / "proj"
    for rel in (".claude/settings.json", ".github/copilot/settings.json"):
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(json.dumps(_old_settings()), encoding="utf-8")
    assert _install(project, "--agent", "copilot", "--mode", "plugin", "--yes") == 0
    for rel in (".claude/settings.json", ".github/copilot/settings.json"):
        assert OLD_MARKETPLACE not in _settings(project / rel)["extraKnownMarketplaces"]
        assert PLUGIN_ID in _settings(project / rel)["enabledPlugins"]
