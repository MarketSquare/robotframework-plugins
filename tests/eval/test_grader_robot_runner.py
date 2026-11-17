"""Grader runs through robotcode (spec skill-eval-harness, "Grader runs and
reads results through RobotCode"). Runs only when robotcode is installed."""

from __future__ import annotations

import textwrap
from datetime import UTC, datetime
from pathlib import Path

import pytest

from rf_skill_eval.domain.run import Run
from rf_skill_eval.grader import robot_runner
from rf_skill_eval.grader.robot_runner import RobotcodeMissingError, run_robot
from rf_skill_eval.scoring import deterministic

needs_robotcode = pytest.mark.skipif(
    robot_runner.robotcode_binary() is None, reason="robotcode not installed"
)



def _run(artifacts: Path) -> Run:
    now = datetime.now(UTC)
    return Run(id="r1", task_id="t1", profile_name="treatment", started_at=now,
               finished_at=now, exit_code=0, artifacts_dir=artifacts)


MIXED = textwrap.dedent(
    """\
    *** Test Cases ***
    Passes
        Log    hello
    Fails
        Fail    boom
    Skips
        Skip    not now
    """
)


@needs_robotcode
def test_run_robot_pass(tmp_path: Path) -> None:
    test_file = tmp_path / "t.robot"
    test_file.write_text("*** Test Cases ***\nPass Always\n    Log    hello world\n")
    result = run_robot([test_file], tmp_path / "out")
    assert (result.total_tests, result.passed_tests, result.failed_tests) == (1, 1, 0)
    assert result.all_passed is True


@needs_robotcode
def test_counts_and_messages_from_robotcode(tmp_path: Path) -> None:
    test_file = tmp_path / "t.robot"
    test_file.write_text(MIXED)
    result = run_robot([test_file], tmp_path / "out")
    assert (result.total_tests, result.passed_tests, result.failed_tests, result.skipped_tests) == (3, 1, 1, 1)
    assert result.statuses() == {"Passes": "PASS", "Fails": "FAIL", "Skips": "SKIP"}
    assert result.failures() == ["Fails: boom"]
    assert result.all_passed is False


@needs_robotcode
def test_robot_pass_counts_from_robotcode(tmp_path: Path) -> None:
    # Scenario "Counts from RobotCode".
    run = _run(tmp_path)
    (tmp_path / "t.robot").write_text(MIXED)
    verdict = deterministic.check_robot_pass(run, "robot_pass", {"path": "t.robot"})
    assert verdict.status == "failed"
    assert "tests=3 passed=1 failed=1" in verdict.details


def test_robot_pass_skipped_without_robotcode(tmp_path: Path, monkeypatch) -> None:
    # Scenario "RobotCode missing".
    monkeypatch.setattr(robot_runner, "robotcode_binary", lambda: None)
    run = _run(tmp_path)
    (tmp_path / "t.robot").write_text(MIXED)
    for check in (deterministic.check_robot_pass, deterministic.check_robot_dryrun):
        verdict = check(run, "c", {"path": "t.robot"})
        assert verdict.status == "skipped"
        assert "robotcode" in verdict.details


def test_run_robot_raises_without_robotcode(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(robot_runner, "robotcode_binary", lambda: None)
    with pytest.raises(RobotcodeMissingError):
        run_robot([tmp_path / "t.robot"], tmp_path / "out")
