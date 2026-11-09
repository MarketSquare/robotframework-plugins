"""Partial-install tier (split-rf-agentskills task 6.2): the grader and the coverage check."""
from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from rf_skill_eval.application.catalog import coverage, plugin_evals_dir
from rf_skill_eval.domain.run import Run
from rf_skill_eval.scoring.custom.partial_install import suggests_plugin, suggests_plugin_or_passes

_REPO = Path(__file__).resolve().parents[2]


def _run(tmp_path: Path, text: str) -> Run:
    session = tmp_path / "session.jsonl"
    session.write_text(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": text}]}}) + "\n")
    workspace = tmp_path / "ws"
    workspace.mkdir(exist_ok=True)
    return Run(id="r", task_id="t", profile_name="treatment", started_at=datetime.now(UTC),
               session_jsonl_path=session, artifacts_dir=tmp_path, workspace_dir=workspace)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("The Browser skill isn't loaded. Install the rf-web plugin: /plugin install rf-web@robotframework-plugins",
         True),
        ("I can't find a web skill. Please install rf-web first.", True),
        ("Here is the test.\nrf-web is a plugin.", False),
        ("Install the plugin for web tests.", False),
    ],
)
def test_suggests_plugin(text: str, expected: bool) -> None:
    assert suggests_plugin(text, "rf-web") is expected


def test_passes_when_it_suggests_the_plugin(tmp_path: Path) -> None:
    run = _run(tmp_path, "rf-browser is not available here; install the rf-web plugin to get it.")
    result = suggests_plugin_or_passes(run, {"plugin": "rf-web"})
    assert result == {"passed": True, "details": "suggests installing rf-web"}


def test_falls_back_to_the_gating_check(tmp_path: Path) -> None:
    run = _run(tmp_path, "Done, the test is written.")
    (run.workspace_dir / "tests").mkdir()
    (run.workspace_dir / "tests" / "login.robot").write_text("*** Test Cases ***\nT\n    Log    x\n")
    ok = suggests_plugin_or_passes(run, {"plugin": "rf-web", "check": {
        "type": "file_contains", "path": "tests/login.robot", "regex": "Log"}})
    assert ok["passed"] is True and "file_contains: passed" in ok["details"]
    bad = suggests_plugin_or_passes(run, {"plugin": "rf-web", "check": {
        "type": "file_contains", "path": "tests/login.robot", "regex": "New Browser"}})
    assert bad["passed"] is False and "does not suggest installing rf-web" in bad["details"]


def test_every_technology_plugin_has_a_partial_task() -> None:
    evals = plugin_evals_dir(_REPO, "all")
    rep = coverage(_REPO, evals / "tasks", evals / "triggers", "all")
    assert rep.ok, rep.problems
    assert {p.parent.parent.parent.parent.name for p in _REPO.glob("plugins/*/evals/tasks/partial/*.yaml")} == {
        "rf-web", "rf-api", "rf-mobile", "rf-desktop"}


def test_coverage_names_a_plugin_without_a_partial_task(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    shutil.copytree(_REPO / "plugins", root / "plugins", ignore=shutil.ignore_patterns("__pycache__", "tests"))
    shutil.copytree(_REPO / "eval" / "fixtures", root / "eval" / "fixtures")
    shutil.rmtree(root / "plugins" / "rf-mobile" / "evals" / "tasks" / "partial")
    evals = root / "plugins" / "rf-mobile" / "evals"
    rep = coverage(root, evals / "tasks", evals / "triggers", "rf-mobile")
    assert "technology plugin 'rf-mobile' has no partial-install task (tier partial, stage [rf-core])" in rep.problems
