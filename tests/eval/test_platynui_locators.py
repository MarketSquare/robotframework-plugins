"""custom.platynui:locators_ok (fix-desktop-eval-turn-overhead 4.1)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from rf_skill_eval.domain.run import Run
from rf_skill_eval.scoring.custom.platynui import locators_ok

_NAME_TO_ID = {"One": "num1Button", "Two": "num2Button", "Plus": "plusButton", "Equals": "equalButton"}


def _run(workspace: Path) -> Run:
    now = datetime.now(UTC)
    return Run(
        id="r1",
        task_id="t",
        profile_name="treatment",
        started_at=now,
        finished_at=now,
        artifacts_dir=workspace,
        workspace_dir=workspace,
    )


def _check(ws: Path, body: str, *, extra: str = "") -> tuple[str, str]:
    (ws / "tests").mkdir(exist_ok=True)
    (ws / "tests" / "calculator.robot").write_text(
        "*** Settings ***\nLibrary    PlatynUI.BareMetal\n" + extra + "\n*** Test Cases ***\nAdd\n" + body
    )
    v = locators_ok(_run(ws), {"target": "tests/calculator.robot", "name_to_id": _NAME_TO_ID})
    return v.status, v.details


_ID_SUITE = (
    "    Pointer Click    //control:Button[@Id='num1Button']\n"
    "    Pointer Click    //control:Button[@Id='plusButton']\n"
    "    Pointer Click    //control:Button[@Id='num2Button']\n"
    "    Pointer Click    //control:Button[@Id='equalButton']\n"
    "    Get Attribute    //control:Text[@Id='CalculatorResults']    Name\n"
)


def test_id_locators_pass(tmp_path: Path) -> None:
    status, details = _check(tmp_path, _ID_SUITE)
    assert status == "passed", details


def test_plain_automation_id_fails_and_names_the_locator(tmp_path: Path) -> None:
    body = _ID_SUITE.replace("@Id='CalculatorResults'", "@AutomationId='CalculatorResults'")
    status, details = _check(tmp_path, body)
    assert status == "failed"
    assert "//control:Text[@AutomationId='CalculatorResults']" in details
    assert "@Id" in details


def test_english_name_fails_and_names_the_id(tmp_path: Path) -> None:
    body = _ID_SUITE.replace("@Id='num1Button'", "@Name='One'").replace("@Id='num2Button'", '@Name="Two"')
    status, details = _check(tmp_path, body)
    assert status == "failed"
    assert "@Id='num1Button'" in details and "@Id='num2Button'" in details


def test_native_automation_id_is_accepted(tmp_path: Path) -> None:
    body = _ID_SUITE.replace("@Id='CalculatorResults'", "@native:AutomationId='CalculatorResults'")
    assert _check(tmp_path, body)[0] == "passed"


def test_id_or_name_predicate_is_accepted(tmp_path: Path) -> None:
    body = _ID_SUITE.replace("@Id='num1Button'", "@Id='num1Button' or @Name='One'")
    assert _check(tmp_path, body)[0] == "passed"


def test_comments_and_documentation_are_ignored(tmp_path: Path) -> None:
    body = (
        "    [Documentation]    Not //control:Text[@AutomationId='CalculatorResults']\n"
        "    # PlatynUI maps @AutomationId to @Id\n"
        + _ID_SUITE
    )
    assert _check(tmp_path, body)[0] == "passed"


def test_variables_and_resources_are_checked(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "calc.resource").write_text(
        "*** Variables ***\n${DISPLAY}    //control:Text[@AutomationId='CalculatorResults']\n"
    )
    status, details = _check(tmp_path, _ID_SUITE, extra="Resource    calc.resource\n")
    assert status == "failed"
    assert "calc.resource" in details


def test_missing_suite_fails(tmp_path: Path) -> None:
    v = locators_ok(_run(tmp_path), {"target": "tests/none.robot"})
    assert v.status == "failed"
