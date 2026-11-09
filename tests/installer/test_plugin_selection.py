"""``install --plugins`` and ``catalog`` (spec plugin-catalogue)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from robotframework_plugins import transforms as _x
from robotframework_plugins.cli import main


@pytest.fixture(autouse=True)
def _force_node(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_x, "node_available", lambda: True)


def _skills(prefix: Path) -> set[str]:
    return {p.parent.name for p in (prefix / "skills").glob("*/SKILL.md")}


def test_default_install_takes_only_verified_plugins(two_plugin_bundle: Path, fake_home: Path, tmp_path: Path) -> None:
    prefix = tmp_path / "root"
    assert main(["install", "--agent", "claude-code", "--prefix", str(prefix), "--yes"]) == 0
    skills = _skills(prefix)
    assert "rf-browser" in skills
    assert "rf-example" not in skills and "rf-old" not in skills


def test_plugins_flag_selects_plugins(two_plugin_bundle: Path, fake_home: Path, tmp_path: Path) -> None:
    prefix = tmp_path / "root"
    assert main(["install", "--agent", "claude-code", "--prefix", str(prefix), "--yes",
                 "--plugins", "rf-core,rf-web,rf-example"]) == 0
    assert _skills(prefix) == {"rf-language", "rf-setup", "rf-python-library", "rf-browser", "rf-selenium",
                               "rf-example"}


def test_default_skips_the_bundle_and_installs_every_content_plugin(
    two_plugin_bundle: Path, fake_home: Path, tmp_path: Path
) -> None:
    prefix = tmp_path / "root"
    assert main(["install", "--agent", "claude-code", "--prefix", str(prefix), "--yes"]) == 0
    (path,) = list(tmp_path.rglob("installed.json"))
    files = [f for ins in json.loads(path.read_text())["installations"] for f in ins["files"]]
    assert {f["plugin"] for f in files} == {"rf-core", "rf-web", "rf-api", "rf-mobile", "rf-desktop"}
    assert len(_skills(prefix)) == 9


def test_bundle_in_file_mode_installs_its_plugins(two_plugin_bundle: Path, fake_home: Path, tmp_path: Path) -> None:
    """``--plugins rf-agentskills`` copies the content of the five plugins it depends on."""
    prefix = tmp_path / "root"
    assert main(["install", "--agent", "claude-code", "--prefix", str(prefix), "--yes",
                 "--plugins", "rf-agentskills"]) == 0
    assert len(_skills(prefix)) == 9
    assert (prefix / "rf-core-files" / "scripts").is_dir()
    assert not (prefix / "rf-agentskills-files").exists()


def test_unknown_plugin_is_refused(
    two_plugin_bundle: Path, fake_home: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    prefix = tmp_path / "root"
    assert main(["install", "--agent", "claude-code", "--prefix", str(prefix), "--yes",
                 "--plugins", "rf-nope"]) != 0
    err = " ".join(capsys.readouterr().err.split())
    assert "rf-nope" in err and "rf-core" in err and "rf-example" in err
    assert not prefix.exists() or not any(prefix.rglob("*"))


def test_deprecated_plugin_warns_with_replacement(
    two_plugin_bundle: Path, fake_home: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    prefix = tmp_path / "root"
    assert main(["install", "--agent", "claude-code", "--prefix", str(prefix), "--yes",
                 "--plugins", "rf-old"]) == 0
    err = " ".join(capsys.readouterr().err.split())
    assert "rf-old is deprecated" in err and "use rf-example" in err
    assert _skills(prefix) == {"rf-old"}


def test_deselected_plugin_is_removed_on_reinstall(two_plugin_bundle: Path, fake_home: Path, tmp_path: Path) -> None:
    prefix = tmp_path / "root"
    assert main(["install", "--agent", "claude-code", "--prefix", str(prefix), "--yes",
                 "--plugins", "rf-core,rf-web,rf-example"]) == 0
    assert main(["install", "--agent", "claude-code", "--prefix", str(prefix), "--yes",
                 "--plugins", "rf-core,rf-web"]) == 0
    assert "rf-example" not in _skills(prefix) and "rf-browser" in _skills(prefix)


def test_plugin_mode_enables_each_selected_plugin(two_plugin_bundle: Path, fake_home: Path, tmp_path: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    assert main(["install", "--scope", "project", "--project", str(project), "--agent", "claude-code",
                 "--mode", "plugin", "--yes", "--plugins", "rf-core,rf-web"]) == 0
    enabled = json.loads((project / ".claude" / "settings.json").read_text())["enabledPlugins"]
    assert enabled == {"rf-core@robotframework-plugins": True, "rf-web@robotframework-plugins": True}


def test_catalog_json(two_plugin_bundle: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["catalog", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["installer"]
    by_name = {p["name"]: p for p in data["plugins"]}
    assert set(by_name) == {"rf-agentskills", "rf-core", "rf-web", "rf-api", "rf-mobile", "rf-desktop",
                            "rf-example", "rf-old"}
    assert by_name["rf-agentskills"]["bundle"] is True
    assert by_name["rf-agentskills"]["bundled"] == ["rf-core", "rf-web", "rf-api", "rf-mobile", "rf-desktop"]
    assert by_name["rf-web"]["dependencies"] == ["rf-core"]
    for p in by_name.values():
        assert {"name", "version", "tier", "status", "summary"} <= set(p)
    assert by_name["rf-old"]["replacement"] == "rf-example"


def test_catalog_table(two_plugin_bundle: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["catalog"]) == 0
    out = capsys.readouterr().out
    assert "rf-example" in out and "community" in out and "deprecated" in out


def test_wizard_offers_plugins_with_tier_and_status(
    two_plugin_bundle: Path, fake_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import builtins
    import sys

    monkeypatch.setitem(sys.modules, "questionary", None)  # force the stdlib selector
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    from robotframework_plugins import _assets
    pick = [p["name"] for p in _assets.bundled_catalog()].index("rf-example") + 1
    answers = iter([str(pick)])  # --agent skips the agent step; plugins: pick rf-example
    shown: list[str] = []
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(answers))
    from robotframework_plugins import cli
    monkeypatch.setattr(cli.console, "print", lambda *a, **k: shown.append(" ".join(map(str, a))))
    prefix = tmp_path / "root"
    assert main(["install", "--agent", "claude-code", "--prefix", str(prefix)]) == 0
    assert any("rf-example (community)" in line for line in shown)
    assert any("rf-old (community, deprecated)" in line for line in shown)
    assert _skills(prefix) == {"rf-example"}
