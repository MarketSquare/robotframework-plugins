"""scripts/desktop-live-check.py: collection and screening (fix-desktop-eval-turn-overhead 9.1).

Runs on any platform: nothing here needs PlatynUI or a desktop.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("desktop_live_check", ROOT / "scripts" / "desktop-live-check.py")
dlc = importlib.util.module_from_spec(_spec)
sys.modules["desktop_live_check"] = dlc
_spec.loader.exec_module(dlc)

_SAFE = """*** Settings ***
Documentation    Does not import anything, nor eval.
Library    PlatynUI.BareMetal

*** Test Cases ***
Add
    Pointer Click    //control:Button[@Id='num1Button']
    Get Attribute    //control:Text[@Id='CalculatorResults']    Name    contains    3
"""


def _session(root: Path, name: str, suite: str = _SAFE) -> Path:
    tests = root / "_temp" / "eval-runs" / "full" / name.split("-", 1)[0] / name / "workspace" / "tests"
    tests.mkdir(parents=True)
    (tests / "calculator.robot").write_text(suite, encoding="utf-8")
    (tests / "example.robot").write_text("*** Test Cases ***\nT\n    Log    stub\n", encoding="utf-8")
    return tests / "calculator.robot"


def test_collects_the_task_suite_per_platynui_session(tmp_path: Path) -> None:
    _session(tmp_path, "narrow-platynui-calculator-01-baseline-aaaa")
    _session(tmp_path, "partial-platynui-calculator-01-treatment-bbbb")
    _session(tmp_path, "narrow-appium-login-01-treatment-cccc")
    suites = dlc.collect(tmp_path)
    assert [(s.tier, s.arm, s.path.name) for s in suites] == [
        ("narrow", "baseline", "calculator.robot"),
        ("partial", "treatment", "calculator.robot"),
    ]


def test_safe_suite_passes_the_screen(tmp_path: Path) -> None:
    path = _session(tmp_path, "narrow-platynui-calculator-01-baseline-aaaa")
    assert dlc.screen(path, root=path.parents[1]) == ""


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (("Library    PlatynUI.BareMetal", "Library    PlatynUI.BareMetal\nLibrary    OperatingSystem"),
         "imports library OperatingSystem"),
        (("    Pointer Click", "    ${x}=    Evaluate    1 + 1\n    Pointer Click"), "calls Evaluate"),
        (("    Pointer Click", "    Run Process    calc.exe\n    Pointer Click"), "calls Run Process"),
        (("    Pointer Click", "    Should Be True    ${{ __import__('os') }}\n    Pointer Click"),
         "unsafe expression"),
        (("Library    PlatynUI.BareMetal", "Library    PlatynUI.BareMetal\nVariables    vars.py"),
         "imports variables"),
    ],
)
def test_unsafe_suite_is_skipped_with_a_reason(tmp_path: Path, change: tuple[str, str], reason: str) -> None:
    path = _session(tmp_path, "narrow-platynui-calculator-01-baseline-aaaa", _SAFE.replace(*change, 1))
    assert reason in dlc.screen(path, root=path.parents[1])


def test_resources_are_screened_and_must_stay_in_the_workspace(tmp_path: Path) -> None:
    path = _session(tmp_path, "narrow-platynui-calculator-01-baseline-aaaa",
                    _SAFE.replace("Library    PlatynUI.BareMetal", "Library    PlatynUI.BareMetal\nResource    calc.resource"))
    (path.parent / "calc.resource").write_text("*** Settings ***\nLibrary    OperatingSystem\n", encoding="utf-8")
    assert "imports library OperatingSystem" in dlc.screen(path, root=path.parents[1])
    outside = _session(tmp_path, "narrow-platynui-calculator-01-baseline-bbbb",
                       _SAFE.replace("Library    PlatynUI.BareMetal",
                                     "Library    PlatynUI.BareMetal\nResource    ../../../../x.resource"))
    (tmp_path / "_temp" / "x.resource").write_text("*** Keywords ***\nK\n    Log    x\n", encoding="utf-8")
    assert "outside the session workspace" in dlc.screen(outside, root=outside.parents[1])


def test_the_skill_example_passes_its_screen() -> None:
    assert dlc.SKILL_EXAMPLE.is_file()
    assert dlc.screen(dlc.SKILL_EXAMPLE, allowed=dlc.EXAMPLE_LIBRARIES, banned=dlc.EXAMPLE_BANNED) == ""
    assert "Process" in dlc.screen(dlc.SKILL_EXAMPLE)  # not allowed for eval suites


def test_list_mode_reports_per_tier_and_arm(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _session(tmp_path, "narrow-platynui-calculator-01-baseline-aaaa")
    _session(tmp_path, "narrow-platynui-calculator-01-treatment-bbbb",
             _SAFE.replace("    Pointer Click", "    Evaluate    1\n    Pointer Click", 1))
    assert dlc.main([str(tmp_path), "--list"]) == 0
    out = capsys.readouterr().out
    assert "narrow   baseline        1" in out
    assert "skipped (not run):" in out and "calls Evaluate" in out
