"""Custom grader checks for the rf-bdd tasks (add-rf-bdd-skill, task 5.2)."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from rf_skill_eval.domain.run import Run
from rf_skill_eval.scoring.custom import bdd
from rf_skill_eval.scoring.deterministic import check_custom_python

_REPO = Path(__file__).resolve().parents[2]
_FIXTURE = _REPO / "eval" / "fixtures" / "sut-bdd-library"

pytest.importorskip("robot")


def _run(tmp_path: Path, ws: Path) -> Run:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir(exist_ok=True)
    now = datetime.now(UTC)
    return Run(id="r", task_id="t", profile_name="treatment", started_at=now,
               artifacts_dir=artifacts, workspace_dir=ws)


def _ws(tmp_path: Path, files: dict[str, str], variant: str = "base") -> Path:
    ws = tmp_path / "ws"
    shutil.copytree(_FIXTURE / variant, ws)
    for rel, text in files.items():
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).write_text(text, encoding="utf-8")
    return ws


_STEPS = """\
*** Settings ***
Documentation       Steps.
Library             LibraryService


*** Variables ***
${LAST_LOAN}        ${None}


*** Keywords ***
The library has a copy of "${title}"
    [Documentation]    One copy on the shelf.
    Add Book    ${title}    1

${member} is a standard member
    [Documentation]    Registers a standard member.
    Register Member    ${member}

${member} borrows "${title}"
    [Documentation]    Borrows today.
    ${result}    Borrow    ${member}    ${title}
    VAR    ${LAST_LOAN}    ${result}    scope=TEST

The loan is granted
    [Documentation]    The last loan was granted.
    Should Be Equal    ${LAST_LOAN}[status]    lent

Borrowing "${title}" is ${status}
    [Documentation]    Outline: Mia borrows ``title``.
    Given the library has a copy of "${title}"
    And Mia is a standard member
    When Mia borrows "${title}"
    Then Should Be Equal    ${LAST_LOAN}[status]    ${status}
"""

_SETTINGS = """\
*** Settings ***
Documentation       As a member I want to borrow books.
Metadata            Feature    Borrowing
Resource            steps.resource
"""

_GOOD = _SETTINGS + """

*** Test Cases ***
Member borrows an available book
    [Documentation]    Rule: an available copy is lent.
    [Tags]    rule:loan
    # a comment is fine
    Given the library has a copy of "Dune"
    And Mia is a standard member
    When Mia borrows "Dune"
    Then the loan is granted
"""

_TEMPLATED = _SETTINGS + """\
Test Template       Borrowing "${title}" is ${status}


*** Test Cases ***                      TITLE       STATUS
Dune is lent                            Dune        lent
Emma is lent                            Emma        lent

Spelled out
    [Template]    NONE
    Given the library has a copy of "Dune"
    And Mia is a standard member
    When Mia borrows "Dune"
    Then the loan is granted
"""


def _project(tmp_path: Path, suite: str, **extra: str) -> Path:
    return _ws(tmp_path, {"resources/steps.resource": _STEPS, "tests/borrowing.robot": suite, **extra})


# --- structure ---------------------------------------------------------------------


def test_structure_passes_for_steps_and_template_rows(tmp_path: Path) -> None:
    ws = _project(tmp_path, _GOOD, **{"tests/outline.robot": _TEMPLATED})
    v = bdd.structure(_run(tmp_path, ws), {"path": "tests"})
    assert v.status == "passed", v.details
    assert "4 tests" in v.details


@pytest.mark.parametrize(
    ("line", "label"),
    [
        ("    Add Book    Dune    1", "Add Book"),
        ("    ${loan}    When Mia borrows \"Dune\"", "When Mia borrows"),
        ("    VAR    ${x}    1", "Var"),
        ("    IF    True    Log    x", "If"),
        ("    Givenish step", "Givenish step"),
    ],
)
def test_structure_fails_on_non_step_lines(tmp_path: Path, line: str, label: str) -> None:
    ws = _project(tmp_path, _GOOD + line + "\n")
    v = bdd.structure(_run(tmp_path, ws), {"path": "tests"})
    assert v.status == "failed"
    assert "tests/borrowing.robot:" in v.details and label in v.details


def test_structure_rejects_keyword_calls_in_a_test_that_turns_the_template_off(tmp_path: Path) -> None:
    suite = _TEMPLATED.replace('    Given the library has a copy of "Dune"', "    Add Book    Dune    1")
    ws = _project(tmp_path, suite)
    v = bdd.structure(_run(tmp_path, ws), {"path": "tests"})
    assert v.status == "failed" and "Spelled out" in v.details


def test_structure_accepts_localised_prefixes(tmp_path: Path) -> None:
    suite = "Language: German\n\n" + _GOOD.replace("Given the", "Angenommen the").replace("When Mia", "Wenn Mia")
    ws = _project(tmp_path, suite)
    v = bdd.structure(_run(tmp_path, ws), {"path": "tests"})
    assert v.status == "passed", v.details


def test_structure_fails_without_tests(tmp_path: Path) -> None:
    ws = _ws(tmp_path, {})
    v = bdd.structure(_run(tmp_path, ws), {"path": "tests"})
    assert v.status == "failed" and "no test cases" in v.details


# --- living_docs -------------------------------------------------------------------


def test_living_docs_passes_with_documentation_and_metadata(tmp_path: Path) -> None:
    ws = _project(tmp_path, _GOOD)
    assert bdd.living_docs(_run(tmp_path, ws), {}).status == "passed"


def test_living_docs_accepts_a_feature_tag_instead_of_metadata(tmp_path: Path) -> None:
    suite = _GOOD.replace("Metadata            Feature    Borrowing", "Test Tags           feature:borrowing")
    ws = _project(tmp_path, suite)
    v = bdd.living_docs(_run(tmp_path, ws), {})
    assert v.status == "passed", v.details


def test_living_docs_inherits_from_init(tmp_path: Path) -> None:
    init = "*** Settings ***\nDocumentation    As a member I want to borrow.\nMetadata    Feature    Borrowing\n"
    suite = _GOOD.replace("Documentation       As a member I want to borrow books.\n", "").replace(
        "Metadata            Feature    Borrowing\n", "").replace("Resource            steps.resource",
                                                               "Resource            steps.resource")
    ws = _ws(tmp_path, {"resources/steps.resource": _STEPS, "tests/borrowing/__init__.robot": init,
                        "tests/borrowing/scenarios.robot": suite})
    v = bdd.living_docs(_run(tmp_path, ws), {})
    assert v.status == "passed", v.details


@pytest.mark.parametrize(
    ("drop", "gap"),
    [
        ("Documentation       As a member I want to borrow books.\n", "no suite Documentation"),
        ("Metadata            Feature    Borrowing\n", "no `Metadata    Feature`"),
    ],
)
def test_living_docs_fails_on_missing_story_or_feature(tmp_path: Path, drop: str, gap: str) -> None:
    ws = _project(tmp_path, _GOOD.replace(drop, ""))
    v = bdd.living_docs(_run(tmp_path, ws), {})
    assert v.status == "failed" and gap in v.details


def test_living_docs_fails_without_suites(tmp_path: Path) -> None:
    ws = _ws(tmp_path, {})
    assert bdd.living_docs(_run(tmp_path, ws), {}).status == "failed"


# --- native_only / step_names_absent ------------------------------------------------


def test_native_only(tmp_path: Path) -> None:
    ws = _project(tmp_path, _GOOD)
    assert bdd.native_only(_run(tmp_path, ws), {}).status == "passed"
    (ws / "features").mkdir()
    (ws / "features" / "borrowing.feature").write_text("Feature: Borrowing\n")
    v = bdd.native_only(_run(tmp_path, ws), {})
    assert v.status == "failed" and "borrowing.feature" in v.details


def test_native_only_flags_a_configured_parser(tmp_path: Path) -> None:
    ws = _project(tmp_path, _GOOD)
    (ws / "robot.toml").write_text((ws / "robot.toml").read_text() + 'parsers = { GherkinParser = [] }\n')
    v = bdd.native_only(_run(tmp_path, ws), {})
    assert v.status == "failed" and "robot.toml" in v.details


def test_step_names_absent_sees_the_runtime_sentence(tmp_path: Path) -> None:
    # The file says "${count} books"; only the run shows "1 books".
    steps = _STEPS + '\n${member} has ${count: int} books\n    [Documentation]    x\n    No Operation\n'
    suite = _GOOD.replace("    Then the loan is granted", "    And Mia has 1 books\n    Then the loan is granted")
    ws = _ws(tmp_path, {"resources/steps.resource": steps, "tests/borrowing.robot": suite})
    run = _run(tmp_path, ws)
    v = bdd.step_names_absent(run, {"path": "tests", "regex": r"(?<![\d.])1 books\b"})
    assert v.status == "failed", v.details
    assert "Mia has 1 books" in v.details
    ok = bdd.step_names_absent(run, {"path": "tests", "regex": r"(?<![\d.])1 days\b", "name": "days"})
    assert ok.status == "passed", ok.details


def test_step_names_absent_fails_a_failing_run(tmp_path: Path) -> None:
    ws = _project(tmp_path, _GOOD.replace("Then the loan is granted", "Then Fail    broken"))
    v = bdd.step_names_absent(_run(tmp_path, ws), {"path": "tests", "regex": "x"})
    assert v.status == "failed" and "run failed" in v.details


# --- review_findings ---------------------------------------------------------------

_SEEDED = ["L1", "L2", "W1", "W2|C5", "W3", "L6", "W12|W6|W7"]


def _transcript(run: Run, text: str, *, result: bool = True) -> None:
    events = [{"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}]
    if result:
        events.append({"type": "result", "subtype": "success", "result": text})
    (run.artifacts_dir / "stdout.stream.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n")


_FINDINGS = """\
Here is the review.

- L1 — tests/loans.robot:8 — `Register Member` in the test body.
- **L2** – tests/loans.robot:11 – procedural UI step.
### S3 · W1 — tests/loans.robot:10 — conjunction step.
1. W3/W12 — tests/loans.robot:7-9 — placeholders and a procedural name.
"""


def _review(tmp_path: Path, text: str | None, **files: str) -> tuple[Run, dict[str, object]]:
    ws = _ws(tmp_path, files, variant="review")
    run = _run(tmp_path, ws)
    if text is not None:
        _transcript(run, text)
    return run, {"fixture": "sut-bdd-library/review", "seeded": _SEEDED, "min_found": 4}


def test_review_findings_counts_findings_lines(tmp_path: Path) -> None:
    run, params = _review(tmp_path, _FINDINGS)
    v = bdd.review_findings(run, params)
    assert v.status == "passed", v.details
    # "W3/W12" names two seeded issues
    assert "found 5/7" in v.details and "W12|W6|W7" in v.details and "missed=['C5|W2', 'L6']" in v.details


def test_review_findings_ignores_ids_outside_the_format(tmp_path: Path) -> None:
    prose = ("L1: library calls in tests/loans.robot. W1 and W3 apply too, see line 10.\n"
             "L2 — the UI step — rewrite it\n"
             "- W2 — loans.robot — vague\n")
    run, params = _review(tmp_path, prose)
    v = bdd.review_findings(run, params)
    assert v.status == "failed"
    assert "0 findings lines" in v.details


def test_review_findings_needs_min_found(tmp_path: Path) -> None:
    run, params = _review(tmp_path, _FINDINGS)
    v = bdd.review_findings(run, {**params, "min_found": 6})
    assert v.status == "failed" and "need 6" in v.details


def test_review_findings_fails_on_any_edit(tmp_path: Path) -> None:
    run, params = _review(tmp_path, _FINDINGS, **{"tests/loans.robot": "*** Test Cases ***\n"})
    v = bdd.review_findings(run, params)
    assert v.status == "failed" and "modified tests/loans.robot" in v.details
    run2, _ = _review(tmp_path / "2", _FINDINGS, **{"REVIEW.md": "notes"})
    v2 = bdd.review_findings(run2, params)
    assert v2.status == "failed" and "added REVIEW.md" in v2.details


def test_review_findings_ignores_tool_output_and_agent_dirs(tmp_path: Path) -> None:
    run, params = _review(tmp_path, _FINDINGS, **{
        "results/output.xml": "<robot/>", ".claude/skills/x/SKILL.md": "x",
        ".robotcode_cache/c.db": "x", "sut/__pycache__/LibraryService.cpython-312.pyc": "x",
        "library_lending.egg-info/PKG-INFO": "x", "uv.lock": "version = 1",
    })
    assert bdd.review_findings(run, params).status == "passed"


def test_changed_files_counts_a_lock_file_the_fixture_has(tmp_path: Path) -> None:
    fixture = _ws(tmp_path, {"uv.lock": "version = 1"}, variant="review")
    ws = tmp_path / "agent"
    shutil.copytree(fixture, ws)
    (ws / "uv.lock").write_text("version = 2", encoding="utf-8")
    assert bdd.changed_files(fixture, ws) == ["modified uv.lock"]


def test_review_findings_uses_the_last_text_without_a_result_line(tmp_path: Path) -> None:
    run, params = _review(tmp_path, None)
    _transcript(run, _FINDINGS, result=False)
    assert bdd.review_findings(run, params).status == "passed"


def test_review_findings_skipped_without_transcript(tmp_path: Path) -> None:
    run, params = _review(tmp_path, None)
    assert bdd.review_findings(run, params).status == "skipped"


def test_finding_lines_parse_ids() -> None:
    lines = bdd.finding_lines(_FINDINGS)
    assert [sorted(ids) for ids, _ in lines] == [["L1"], ["L2"], ["W1"], ["W12", "W3"]]


def test_checks_resolve_through_custom_python(tmp_path: Path) -> None:
    ws = _project(tmp_path, _GOOD)
    for func in ("structure", "living_docs", "native_only"):
        v = check_custom_python(_run(tmp_path, ws), func,
                                {"func_ref": f"rf_skill_eval.scoring.custom.bdd:{func}", "path": "tests"})
        assert v.status == "passed", (func, v.details)


# --- fixture -----------------------------------------------------------------------


def test_fixture_variants_are_the_base_plus_their_files() -> None:
    base = {p.relative_to(_FIXTURE / "base") for p in (_FIXTURE / "base").rglob("*") if p.is_file()}
    shared = {p for p in base if p.name not in ("README.md", ".gitkeep")}
    for variant in ("steps", "review"):
        root = _FIXTURE / variant
        for rel in shared:
            assert (root / rel).read_bytes() == (_FIXTURE / "base" / rel).read_bytes(), (variant, rel)
    assert not [p for p in (_FIXTURE / "base" / "tests").iterdir() if p.name != ".gitkeep"]
    assert (_FIXTURE / "steps" / "resources" / "borrowing_steps.resource").is_file()
    review = (_FIXTURE / "review" / "tests" / "loans.robot").read_text()
    for seeded in ("Register Member    user1", "presses borrow", "is registered and the library has",
                   "Then everything is fine", "Check stuff"):
        assert seeded in review, seeded


def test_review_variant_is_unchanged_against_itself() -> None:
    assert bdd.changed_files(_FIXTURE / "review", _FIXTURE / "review") == []
