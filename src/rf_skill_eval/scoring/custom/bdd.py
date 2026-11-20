"""Custom grader checks for the rf-bdd eval tasks (add-rf-bdd-skill D10).

Referenced from task YAML as ``custom_python`` with
``func_ref: rf_skill_eval.scoring.custom.bdd:<function>``. Every function
takes ``(run, params)`` and returns a tri-state :class:`Verdict`; a check that
cannot run (Robot Framework or robotcode missing in the grader environment) is
``skipped`` with a reason, never passed.

* :func:`structure` — test bodies hold only BDD-prefixed step calls, or
  template rows in templated tests (AST via ``robot.api``).
* :func:`living_docs` — every suite with tests has suite documentation and
  ``Metadata    Feature`` or a ``feature:`` tag (own or from ``__init__.robot``).
* :func:`native_only` — no ``.feature`` file and no parser configured.
* :func:`step_names_absent` — a real run whose executed step names never
  match a regex (the outline row that reads "1 days").
* :func:`review_findings` — no file changed against the fixture, and the
  final message has at least N findings lines ``ID — file:line — …`` naming
  seeded check IDs.

The workspace fixtures are ``eval/fixtures/sut-bdd-library/<variant>``: a
``base`` project and the ``steps`` / ``review`` variants, which are the base
plus the files of that variant (the harness copies one fixture directory, so
an "overlay" is a variant directory selected by the task's ``fixture``).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from ...domain.run import Run
from ...domain.verdict import Verdict
from ...grader.robot_runner import RobotcodeMissingError, run_robot
from ..session_based import _resolve_transcript

_REPO = Path(__file__).resolve().parents[4]
FIXTURES_DIR = _REPO / "eval" / "fixtures"

#: Settings a BDD test may carry besides its steps.
_ALLOWED_SETTINGS = ("Documentation", "Tags", "Setup", "Teardown", "Template", "Timeout")
#: Directories never part of the project's own files (agent tooling, caches, run output,
#: and the ``*.egg-info`` that ``uv run`` builds for the fixture project).
_IGNORED_DIRS = {"results", "__pycache__", "node_modules", "grader-out"}
_IGNORED_FILES = {"output.xml", "log.html", "report.html"}

#: A findings line: ``L1 — tests/loans.robot:8 — …`` (also ``- **L1** – file:8-9 - …``,
#: ``S2 · L1 — …``, ``W3/W12 — …``). The ID part is captured, the location must name
#: a file with an extension and a line number.
_FINDING = re.compile(
    r"""^\s*(?:[-*+]|\d+[.)]|\#{1,6})?\s*      # list marker or heading
        (?:\*\*|`)?\s*(?:S\d\s*[·.:]\s*)?       # optional bold/code and severity
        (?P<ids>[A-Z]\d{1,2}(?:\s*[/,+&]\s*[A-Z]\d{1,2})*)
        \s*(?:\*\*|`)?\s*
        (?:—|–|-{1,2})\s*                       # separator
        (?:\*\*|`)?(?P<loc>[\w./\\-]+\.\w+:\d+(?:\s*[-–]\s*\d+)?)(?:\*\*|`)?
        \s*(?:—|–|-{1,2})\s*\S                   # separator and some text
    """,
    re.VERBOSE,
)
_ID = re.compile(r"[A-Z]\d{1,2}")


def _name(params: dict[str, Any], default: str) -> str:
    return str(params.get("name") or default)


def _hidden(rel: Path) -> bool:
    return any(part.startswith(".") or part in _IGNORED_DIRS or part.endswith(".egg-info")
               for part in rel.parts[:-1])


def _robot_files(ws: Path, params: dict[str, Any]) -> list[Path]:
    root = ws / str(params.get("path", "tests"))
    if root.is_file():
        return [root]
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*.robot") if p.is_file() and not _hidden(p.relative_to(ws)))


def _bdd_prefixes() -> set[str]:
    """BDD prefixes of every built-in language, lowercased."""
    from robot.conf.languages import Language

    prefixes: set[str] = set()
    for cls in Language.__subclasses__():
        try:
            prefixes |= {p.lower() for p in cls().bdd_prefixes}
        except Exception:  # a broken language class must not break grading
            continue
    return prefixes or {"given", "when", "then", "and", "but"}


def _settings(model: Any) -> dict[str, Any]:
    from robot.api.parsing import Documentation, Metadata, TestTags

    found: dict[str, Any] = {"documentation": False, "feature_metadata": False, "test_tags": []}
    for section in model.sections:
        if type(section).__name__ != "SettingSection":
            continue
        for node in section.body:
            if isinstance(node, Documentation):
                found["documentation"] = bool(node.value.strip())
            elif isinstance(node, Metadata) and node.name.strip().lower() == "feature" and node.value.strip():
                found["feature_metadata"] = True
            elif isinstance(node, TestTags):
                found["test_tags"] += list(node.values)
    return found


def _inherited(path: Path, ws: Path) -> dict[str, Any]:
    """Settings from the ``__init__.robot`` files between the workspace and ``path``."""
    from robot.api import get_model

    merged: dict[str, Any] = {"documentation": False, "feature_metadata": False, "test_tags": []}
    for parent in path.parents:
        if parent != ws and ws not in parent.parents:
            break
        init = parent / "__init__.robot"
        if init.is_file() and init != path:
            s = _settings(get_model(init))
            merged["documentation"] |= s["documentation"]
            merged["feature_metadata"] |= s["feature_metadata"]
            merged["test_tags"] += s["test_tags"]
    return merged


def _tests(model: Any) -> list[Any]:
    return [t for s in model.sections if type(s).__name__ == "TestCaseSection"
            for t in s.body if hasattr(t, "name") and hasattr(t, "body")]


def _parse(files: list[Path]) -> list[tuple[Path, Any]]:
    from robot.api import get_model

    return [(p, get_model(p)) for p in files if p.name != "__init__.robot"]


def _robot_missing(run: Run, name: str) -> Verdict | None:
    try:
        import robot.api  # noqa: F401
    except ImportError:
        return Verdict.skipped(run.id, name, "robotframework not importable in the grader environment")
    return None


def _non_step_lines(test: Any, suite_template: bool, prefixes: set[str]) -> list[tuple[int, str]]:
    """``(lineno, label)`` of each body line that is neither a BDD step nor a template row."""
    from robot.api.parsing import KeywordCall, Template, TemplateArguments

    templated = suite_template
    for node in test.body:
        if isinstance(node, Template):
            templated = node.value not in (None, "", "NONE")
    found: list[tuple[int, str]] = []
    for node in test.body:
        kind = type(node).__name__
        if kind in ("EmptyLine", "Comment") or kind in _ALLOWED_SETTINGS:
            continue
        if isinstance(node, TemplateArguments) and templated:
            continue
        if isinstance(node, KeywordCall) and not node.assign:
            words = (node.keyword or "").strip().lower()
            if any(words.startswith(f"{p} ") for p in prefixes):
                continue
        found.append((node.lineno, node.keyword if isinstance(node, KeywordCall) else kind))
    return found


def structure(run: Run, params: dict[str, Any]) -> Verdict:
    """Test bodies hold only ``Given/When/Then/And/But …`` calls or template rows.

    Params: ``path`` (workspace-relative file or directory, default ``tests``).
    A call that assigns a variable, a ``VAR``, ``IF``/``FOR`` block or a
    library keyword in a test body fails it; settings (``[Documentation]``,
    ``[Tags]``, ``[Setup]``, ``[Teardown]``, ``[Template]``, ``[Timeout]``),
    comments and empty lines are allowed. Fails when no test is found.
    """
    name = _name(params, "bdd_structure")
    if (missing := _robot_missing(run, name)) is not None:
        return missing
    from robot.api.parsing import TestTemplate

    ws = run.effective_workspace
    prefixes = _bdd_prefixes()
    problems: list[str] = []
    seen = 0
    for path, model in _parse(_robot_files(ws, params)):
        suite_template = any(isinstance(n, TestTemplate) and n.value not in (None, "", "NONE")
                             for s in model.sections if type(s).__name__ == "SettingSection" for n in s.body)
        rel = path.relative_to(ws)
        for test in _tests(model):
            seen += 1
            problems += [f"{rel}:{line} '{test.name}': {label}"
                         for line, label in _non_step_lines(test, suite_template, prefixes)]
    if not seen:
        return Verdict.of(run.id, name, False, f"no test cases under {params.get('path', 'tests')}")
    return Verdict.of(run.id, name, not problems,
                      f"{seen} tests, {len(problems)} non-step lines" + (f": {problems[:6]}" if problems else ""))


def living_docs(run: Run, params: dict[str, Any]) -> Verdict:
    """Every suite file with tests has documentation and a feature marker.

    The marker is ``Metadata    Feature    …`` or a ``feature:`` tag (``Test
    Tags`` of the suite, or ``[Tags]`` of every test); both may come from an
    ``__init__.robot`` above the file. Params: ``path`` (default ``tests``).
    """
    name = _name(params, "bdd_living_docs")
    if (missing := _robot_missing(run, name)) is not None:
        return missing
    from robot.api.parsing import Tags

    ws = run.effective_workspace
    gaps: list[str] = []
    suites = 0
    for path, model in _parse(_robot_files(ws, params)):
        tests = _tests(model)
        if not tests:
            continue
        suites += 1
        own, parent = _settings(model), _inherited(path, ws)
        rel = path.relative_to(ws)
        if not (own["documentation"] or parent["documentation"]):
            gaps.append(f"{rel}: no suite Documentation")
        suite_tags = [t.lower() for t in own["test_tags"] + parent["test_tags"]]
        tagged = any(t.startswith("feature:") for t in suite_tags) or all(
            any(str(v).lower().startswith("feature:") for n in t.body if isinstance(n, Tags) for v in n.values)
            for t in tests
        )
        if not (own["feature_metadata"] or parent["feature_metadata"] or tagged):
            gaps.append(f"{rel}: no `Metadata    Feature` and no feature: tag")
    if not suites:
        return Verdict.of(run.id, name, False, f"no suites with tests under {params.get('path', 'tests')}")
    return Verdict.of(run.id, name, not gaps, f"{suites} suites, gaps: {gaps[:6]}" if gaps else f"{suites} suites")


_PARSER_CONFIG = re.compile(r"(?im)^\s*\[(tool\.robot\.)?parsers\]|--parser\b|^\s*parsers\s*=|GherkinParser")


def native_only(run: Run, params: dict[str, Any]) -> Verdict:
    """No ``.feature`` file in the project and no parser configured (``GherkinParser``)."""
    name = _name(params, "native_only")
    ws = run.effective_workspace
    problems = [f"{p.relative_to(ws)}: .feature file" for p in sorted(ws.rglob("*.feature"))
                if p.is_file() and not _hidden(p.relative_to(ws))]
    for rel in ("robot.toml", "pyproject.toml", ".robot.toml"):
        path = ws / rel
        if path.is_file() and _PARSER_CONFIG.search(path.read_text(encoding="utf-8", errors="replace")):
            problems.append(f"{rel}: configures a parser")
    for path in sorted([*ws.rglob("*.robot"), *ws.rglob("*.resource")]):
        if not _hidden(path.relative_to(ws)) and "GherkinParser" in path.read_text(encoding="utf-8", errors="replace"):
            problems.append(f"{path.relative_to(ws)}: GherkinParser")
    return Verdict.of(run.id, name, not problems, f"non-native: {problems[:6]}" if problems else "native .robot only")


def _executed_names(output_xml: Path) -> list[str]:
    from robot.api import ExecutionResult, ResultVisitor

    names: list[str] = []

    class _Collect(ResultVisitor):  # type: ignore[misc]
        def visit_test(self, test: Any) -> None:
            names.append(test.name)
            super().visit_test(test)

        def start_keyword(self, kw: Any) -> None:
            names.append(str(kw.name or ""))

    ExecutionResult(str(output_xml)).visit(_Collect())
    return names


def step_names_absent(run: Run, params: dict[str, Any]) -> Verdict:
    """Run ``path`` and fail when an executed test or keyword name matches ``regex``.

    Catches outline sentences that read wrongly for a row at run time (an
    embedded ``${days} days`` called with ``1``), which the source files do
    not show. Params: ``path`` (default ``tests``), ``regex``. The run itself
    must pass with at least one test.
    """
    name = _name(params, "step_names_absent")
    if (missing := _robot_missing(run, name)) is not None:
        return missing
    ws = run.effective_workspace
    target = ws / str(params.get("path", "tests"))
    if not target.exists():
        return Verdict.of(run.id, name, False, f"missing {params.get('path', 'tests')}")
    pattern = re.compile(str(params["regex"]))
    outdir = run.artifacts_dir / "grader_bdd" / re.sub(r"[^A-Za-z0-9_.-]+", "_", name)[:60]
    try:
        result = run_robot([target], outdir, cwd=ws, timeout_seconds=int(params.get("timeout_seconds", 120)))
    except RobotcodeMissingError:
        return Verdict.skipped(run.id, name, "robotcode not installed")
    if result.timed_out or result.output_xml is None:
        return Verdict.of(run.id, name, False, "robot run timed out or wrote no output.xml")
    if result.returncode != 0 or result.total_tests < 1:
        return Verdict.of(run.id, name, False, f"run failed: exit={result.returncode} tests={result.total_tests}")
    hits = sorted({n for n in _executed_names(result.output_xml) if pattern.search(n)})
    return Verdict.of(run.id, name, not hits,
                      f"regex={pattern.pattern!r} " + (f"matched executed names {hits[:4]}" if hits else "absent"))


# --- review ------------------------------------------------------------------------


def _project_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if not path.is_file() or _hidden(rel) or (rel.name.startswith(".") and rel.name != ".gitignore"):
            continue
        if path.name in _IGNORED_FILES or path.suffix == ".pyc":
            continue
        files[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def changed_files(fixture_dir: Path, workspace: Path) -> list[str]:
    """Files added, removed or modified in ``workspace`` relative to ``fixture_dir``.

    Hidden directories (``.claude``, ``.robotcode_cache``), ``results/``, caches
    and Robot Framework output files are ignored.
    """
    want, got = _project_files(fixture_dir), _project_files(workspace)
    return sorted(
        [f"added {p}" for p in got.keys() - want.keys()]
        + [f"removed {p}" for p in want.keys() - got.keys()]
        + [f"modified {p}" for p in want.keys() & got.keys() if want[p] != got[p]]
    )


def final_message(run: Run) -> str | None:
    """The agent's final answer: the stream's ``result`` text, else its last text block."""
    import json

    path = _resolve_transcript(run)
    if path is None:
        return None
    result: str | None = None
    last_text: str | None = None
    with path.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
                continue
            if entry.get("type") == "result" and isinstance(entry.get("result"), str):
                result = entry["result"]
            message = entry.get("message")
            if isinstance(message, dict) and message.get("role") == "assistant":
                content = message.get("content")
                blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content or []
                texts = [str(b.get("text", "")) for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
                if any(t.strip() for t in texts):
                    last_text = "\n".join(texts)
    return result if result and result.strip() else last_text


def finding_lines(text: str) -> list[tuple[set[str], str]]:
    """``(ids, line)`` for each line in the findings format ``ID — file:line — …``."""
    found: list[tuple[set[str], str]] = []
    for line in text.splitlines():
        match = _FINDING.match(line)
        if match:
            found.append((set(_ID.findall(match.group("ids"))), line.strip()))
    return found


def review_findings(run: Run, params: dict[str, Any]) -> Verdict:
    """Review mode: nothing edited, and at least ``min_found`` seeded issues reported.

    Params: ``fixture`` (fixture directory the workspace was copied from, e.g.
    ``sut-bdd-library/review``), ``seeded`` (one entry per seeded issue; an
    entry is a check ID or ``"W2|C5"`` when either ID names it), ``min_found``
    (default: all). Only lines in the findings format count; an issue is found
    when a findings line names one of its IDs. Skipped without a transcript.
    """
    name = _name(params, "review_findings")
    fixture = FIXTURES_DIR / str(params["fixture"])
    if not fixture.is_dir():
        return Verdict.errored(run.id, name, f"fixture missing: {fixture}")
    changes = changed_files(fixture, run.effective_workspace)
    if changes:
        return Verdict.of(run.id, name, False, f"review changed files: {changes[:6]}")
    text = final_message(run)
    if text is None:
        return Verdict.skipped(run.id, name, "no session transcript (stdout.stream.jsonl missing)")
    seeded = [{i.strip() for i in str(entry).split("|") if i.strip()} for entry in params.get("seeded") or ()]
    if not seeded:
        return Verdict.errored(run.id, name, "review_findings needs a non-empty 'seeded' list")
    want = int(params.get("min_found", len(seeded)))
    lines = finding_lines(text)
    named = set().union(*(ids for ids, _ in lines)) if lines else set()
    found = ["|".join(sorted(entry)) for entry in seeded if entry & named]
    missed = ["|".join(sorted(entry)) for entry in seeded if not entry & named]
    ok = len(found) >= want
    return Verdict.of(run.id, name, ok,
                      f"no edits; {len(lines)} findings lines; seeded found {len(found)}/{len(seeded)} "
                      f"(need {want}): found={found} missed={missed}")
