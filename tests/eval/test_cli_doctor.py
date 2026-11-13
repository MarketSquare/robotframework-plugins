"""CLI smoke tests via Typer's CliRunner."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from typer.testing import CliRunner

from rf_skill_eval.application.catalog import plugin_evals_dir
from rf_skill_eval.cli import app

runner = CliRunner()


def test_doctor_runs(monkeypatch) -> None:
    # Stub the auth ping: a developer's .env token must not trigger a live API call.
    monkeypatch.setattr("rf_skill_eval.cli._claude_auth_ping", lambda _b: (True, "stubbed"))
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "rf-skill-eval doctor" in result.stdout


def test_doctor_fails_when_auth_ping_returns_api_error(monkeypatch) -> None:
    """The whole point of the ping: bad token → exit code 1, not silent pass."""

    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "fake")

    fake_completed = subprocess.CompletedProcess(
        args=["claude"],
        returncode=0,
        stdout='{"type":"result","is_error":true,"result":"API Error: Header has invalid value"}',
        stderr="",
    )
    with patch("rf_skill_eval.cli.shutil.which", return_value="/fake/claude"), patch(
        "rf_skill_eval.cli.subprocess.run", return_value=fake_completed
    ):
        result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "claude auth ping" in result.stdout
    assert "API rejected probe" in result.stdout


def test_doctor_passes_ping_that_stops_at_the_turn_limit(monkeypatch) -> None:
    """A model that answers with a tool call hits --max-turns 1; auth still worked."""
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "fake")
    fake_completed = subprocess.CompletedProcess(
        args=["claude"],
        returncode=1,
        stdout='{"type":"system","subtype":"init"}\n'
        '{"type":"result","subtype":"error_max_turns","is_error":true,"num_turns":2}',
        stderr='{"model":"z-ai/glm-5.3-flash","query_source":"unrecognized_model"}',
    )
    with patch("rf_skill_eval.cli.shutil.which", return_value="/fake/claude"), patch(
        "rf_skill_eval.cli.subprocess.run", return_value=fake_completed
    ):
        result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    row = next(line for line in result.stdout.splitlines() if "claude auth ping" in line)
    assert "ok" in row


def test_doctor_ping_failure_reports_the_result_not_stderr(monkeypatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "fake")
    fake_completed = subprocess.CompletedProcess(
        args=["claude"],
        returncode=1,
        stdout='{"type":"result","subtype":"error_during_execution","is_error":true}',
        stderr='{"model":"x","query_source":"unrecognized_model"}',
    )
    with patch("rf_skill_eval.cli.shutil.which", return_value="/fake/claude"), patch(
        "rf_skill_eval.cli.subprocess.run", return_value=fake_completed
    ):
        result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "error_during_execution" in result.stdout


def test_doctor_passes_ping_with_clean_response(monkeypatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "fake")
    fake_completed = subprocess.CompletedProcess(
        args=["claude"],
        returncode=0,
        stdout='{"type":"result","is_error":false,"result":"ok"}',
        stderr="",
    )
    with patch("rf_skill_eval.cli.shutil.which", return_value="/fake/claude"), patch(
        "rf_skill_eval.cli.subprocess.run", return_value=fake_completed
    ):
        result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "auth verified via claude --print" in result.stdout


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.stdout
    assert "score" in result.stdout
    assert "report" in result.stdout
    assert "doctor" in result.stdout
    assert "bench" in result.stdout


def test_run_missing_task_errors() -> None:
    result = runner.invoke(app, ["run", "--task", "/nonexistent/task.yaml"])
    assert result.exit_code != 0


# --- grader requirements (strengthen-skill-eval-harness 1.6) ---------------------

from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

from rf_skill_eval import cli as cli_module  # noqa: E402

_REPO = Path(__file__).resolve().parents[2]


def _no_ping(monkeypatch) -> None:
    # Never call the real CLI/API from these tests (a local .env may hold a token).
    monkeypatch.setattr(cli_module, "_claude_auth_ping", lambda _b: (True, "stubbed"))


def test_doctor_lists_grader_requirements_of_selected_tasks(monkeypatch) -> None:
    _no_ping(monkeypatch)
    result = runner.invoke(app, ["doctor", "--tasks-dir", str(plugin_evals_dir(_REPO, "all") / "tasks" / "narrow")])
    assert result.exit_code == 0, result.stdout
    for req in ("tool:robot", "module:Browser", "module:SeleniumLibrary", "module:REST"):
        assert f"grader {req}" in result.stdout


def test_doctor_strict_fails_on_missing_grader_library(tmp_path: Path, monkeypatch) -> None:
    _no_ping(monkeypatch)
    tasks = tmp_path / "narrow"
    tasks.mkdir()
    (tasks / "t.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "narrow-x",
                "skill": "rf-results",
                "prompt": "x",
                "primary_metric": "robot_pass",
                "grader_checks": [
                    {"type": "robot_pass", "target": "t.robot", "requires": ["NoSuchLibZz"]},
                    {"type": "lint_clean", "target": "t.robot"},
                ],
            }
        )
    )
    lenient = runner.invoke(app, ["doctor", "--tasks-dir", str(tmp_path)])
    assert lenient.exit_code == 0
    assert "module:NoSuchLibZz" in lenient.stdout
    strict = runner.invoke(app, ["doctor", "--tasks-dir", str(tmp_path), "--strict"])
    assert strict.exit_code == 1


def test_grader_requirements_mapping() -> None:
    from rf_skill_eval.domain.task import Task

    task = Task(
        id="t",
        skill="rf-results",
        prompt="x",
        grader_checks=[
            {"type": "robot_dryrun", "target": "a", "requires": ["AppiumLibrary"]},
            {"type": "lint_clean", "target": "a"},
            {"type": "keywords_resolve", "target": "a", "specs": ["s.json"]},
        ],
    )
    needs = cli_module.grader_requirements([task])
    assert set(needs) == {"tool:robot", "tool:robocop", "module:robot", "module:AppiumLibrary"}
