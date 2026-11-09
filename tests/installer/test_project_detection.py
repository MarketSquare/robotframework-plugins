"""The installer picks plugins from the project (spec plugin-split, "The
installer picks plugins from the project" and the upgrade requirement)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from robotframework_plugins import _assets
from robotframework_plugins.cli import main
from robotframework_plugins.detect import declared_packages, detect

ALL = ("rf-core", "rf-api", "rf-desktop", "rf-mobile", "rf-web")


def _skills(prefix: Path) -> set[str]:
    return {p.parent.name for p in (prefix / "skills").glob("*/SKILL.md")}


def _recorded_plugins(tmp_path: Path) -> set[str]:
    (path,) = list(tmp_path.rglob("installed.json"))
    return {f["plugin"] for ins in json.loads(path.read_text())["installations"] for f in ins["files"]}


def test_browser_project(fake_home: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        '[project]\nname = "p"\ndependencies = ["robotframework-browser>=20", "robotframework-requests"]\n')
    prefix = tmp_path / "root"
    assert main(["install", "--agent", "claude-code", "--project", str(project), "--prefix", str(prefix),
                 "--yes"]) == 0
    assert _recorded_plugins(tmp_path) == {"rf-core", "rf-web", "rf-api"}
    assert {"rf-browser", "rf-requests", "rf-language"} <= _skills(prefix)
    assert not {"rf-appium", "rf-platynui"} & _skills(prefix)
    out = " ".join(capsys.readouterr().out.split())
    assert "robotframework-browser" in out and "robotframework-requests" in out


def test_nothing_detected(fake_home: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    (project / "requirements.txt").write_text("robotframework>=7\n")
    prefix = tmp_path / "root"
    assert main(["install", "--agent", "claude-code", "--project", str(project), "--prefix", str(prefix),
                 "--yes"]) == 0
    assert _recorded_plugins(tmp_path) == set(ALL)
    assert "no library detected" in " ".join(capsys.readouterr().out.split())


def test_plugins_all_selects_every_verified_plugin(fake_home: Path, tmp_path: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    (project / "requirements.txt").write_text("robotframework-browser\n")
    prefix = tmp_path / "root"
    assert main(["install", "--agent", "claude-code", "--project", str(project), "--prefix", str(prefix),
                 "--yes", "--plugins", "all"]) == 0
    assert _recorded_plugins(tmp_path) == set(ALL)


@pytest.mark.parametrize(
    ("name", "text"),
    [
        ("pyproject.toml", '[project.optional-dependencies]\nui = ["robotframework_browser[bb]"]\n'),
        ("pyproject.toml", '[dependency-groups]\ntest = ["Robotframework-Browser ==20.1"]\n'),
        ("pyproject.toml", '[tool.poetry.dependencies]\npython = "^3.12"\nrobotframework-browser = "*"\n'),
        ("pyproject.toml", '[tool.poetry.group.dev.dependencies]\nrobotframework-browser = "*"\n'),
        ("requirements-dev.txt", "# web\n-r base.txt\nrobotframework-browser==20.1 ; python_version>='3.10'\n"),
    ],
)
def test_declaration_forms(tmp_path: Path, name: str, text: str) -> None:
    (tmp_path / name).write_text(text)
    assert declared_packages(tmp_path) == {"robotframework-browser": name}
    found = detect(tmp_path, _assets.bundled_catalog())
    assert found.plugins == ["rf-core", "rf-web"]


def test_bundle_is_never_detected(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("RESTinstance\n")
    found = detect(tmp_path, _assets.bundled_catalog())
    assert found.plugins == ["rf-core", "rf-api"] and "rf-agentskills" not in found.reasons


def test_upgrade_keeps_what_is_installed(fake_home: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A later run without --plugins keeps the plugins of the earlier install,
    even when the project now declares only one library."""
    project = tmp_path / "proj"
    project.mkdir()
    prefix = tmp_path / "root"
    args = ["install", "--agent", "claude-code", "--project", str(project), "--prefix", str(prefix), "--yes"]
    assert main(args) == 0  # nothing declared: everything
    (project / "requirements.txt").write_text("robotframework-browser\n")
    capsys.readouterr()
    assert main(args) == 0
    assert _recorded_plugins(tmp_path) == set(ALL)
    assert "upgrade" in " ".join(capsys.readouterr().out.split())


def test_upgrade_adds_a_newly_declared_library(fake_home: Path, tmp_path: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    prefix = tmp_path / "root"
    args = ["install", "--agent", "claude-code", "--project", str(project), "--prefix", str(prefix), "--yes"]
    assert main([*args, "--plugins", "rf-core,rf-api"]) == 0
    (project / "requirements.txt").write_text("robotframework-browser\n")
    assert main(args) == 0
    assert _recorded_plugins(tmp_path) == {"rf-core", "rf-api", "rf-web"}


def test_plugin_mode_upgrade_keeps_the_bundle(fake_home: Path, tmp_path: Path) -> None:
    """Settings that enable rf-agentskills keep it enabled: the bundle still installs everything."""
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    settings = project / ".claude" / "settings.json"
    settings.write_text(json.dumps({"enabledPlugins": {"rf-agentskills@robotframework-plugins": True}}))
    (project / "requirements.txt").write_text("robotframework-browser\n")
    assert main(["install", "--scope", "project", "--project", str(project), "--agent", "claude-code",
                 "--mode", "plugin", "--yes"]) == 0
    assert json.loads(settings.read_text())["enabledPlugins"] == {"rf-agentskills@robotframework-plugins": True}
