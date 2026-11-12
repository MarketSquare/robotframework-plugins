"""Static locator check for PlatynUI tasks (skill-eval-harness "PlatynUI tasks check locators statically").

The CI runner has no desktop, so ``keywords_resolve`` only proves that the
keywords exist. A live run on Windows (2026-11-12) showed the locators are
where suites fail: PlatynUI exposes the UIA AutomationId as ``@Id`` (a plain
``@AutomationId`` matches nothing), and ``@Name`` follows the display language.

    - type: custom_python
      name: platynui_locators
      func_ref: rf_skill_eval.scoring.custom.platynui:locators_ok
      target: tests/calculator.robot
      name_to_id: {One: num1Button, Plus: plusButton}

The check scans every argument and variable value of the suite and the
resources it imports (comments and documentation are skipped). It fails on
``@AutomationId`` not written as ``@native:AutomationId``, and on a predicate
that matches ``@Name='<value>'`` for a value in ``name_to_id`` without also
accepting an ``@Id`` (``[@Id='num1Button' or @Name='One']`` passes).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from ...domain.run import Run
from ...domain.verdict import Verdict
from .language import _name

_AUTOMATION_ID = re.compile(r"(?<!native:)@AutomationId\b")
_PREDICATE = re.compile(r"\[([^\[\]]*)\]")
_NAME_VALUE = re.compile(r"""@Name\s*=\s*(?:'([^']*)'|"([^"]*)")""")
_ID = re.compile(r"@Id\b")
_SKIPPED_STATEMENTS = frozenset({"DOCUMENTATION", "METADATA", "COMMENT"})


def _suite_files(suite: Path) -> list[Path]:
    """The suite plus the resources it imports, recursively."""
    from robot.api import get_model, get_resource_model
    from robot.api.parsing import ResourceImport

    out: list[Path] = []
    todo = [suite]
    seen: set[Path] = set()
    while todo:
        path = todo.pop()
        real = path.resolve()
        if real in seen or not path.is_file():
            continue
        seen.add(real)
        out.append(path)
        model = get_model(str(path)) if path.suffix == ".robot" else get_resource_model(str(path))
        for node in ast.walk(model):
            if isinstance(node, ResourceImport) and node.name:
                raw = str(node.name).replace("${CURDIR}", str(path.parent))
                todo.append(Path(raw) if Path(raw).is_absolute() else path.parent / raw)
    return out


def _arguments(path: Path) -> list[tuple[str, int]]:
    """(value, line) of every argument token outside comments and documentation."""
    from robot.api import Token, get_model, get_resource_model
    from robot.parsing.model.statements import Statement

    model = get_model(str(path)) if path.suffix == ".robot" else get_resource_model(str(path))
    values: list[tuple[str, int]] = []
    for node in ast.walk(model):
        if not isinstance(node, Statement) or node.type in _SKIPPED_STATEMENTS:
            continue
        values.extend((t.value, t.lineno) for t in node.tokens if t.type == Token.ARGUMENT)
    return values


def locator_problems(value: str, name_to_id: dict[str, str]) -> list[str]:
    """Why ``value`` (one argument) holds a locator that fails on a real desktop."""
    problems: list[str] = []
    if _AUTOMATION_ID.search(value):
        problems.append(f"{value!r} uses @AutomationId; PlatynUI exposes it as @Id")
    for predicate in _PREDICATE.findall(value):
        if _ID.search(predicate):
            continue
        for single, double in _NAME_VALUE.findall(predicate):
            name = single or double
            if name in name_to_id:
                problems.append(
                    f"{value!r} finds {name!r} by its localised @Name; use @Id='{name_to_id[name]}'"
                )
    return problems


def locators_ok(run: Run, params: dict[str, Any]) -> Verdict:
    name = _name(params, "platynui_locators")
    target = params.get("path") or params.get("target")
    if not target:
        return Verdict.errored(run.id, name, "platynui_locators needs 'target'")
    try:
        import robot.api  # noqa: F401
    except ImportError:
        return Verdict.skipped(run.id, name, "Robot Framework is not importable by the grader")
    suite = run.effective_workspace / str(target)
    if not suite.is_file():
        return Verdict.of(run.id, name, False, f"suite missing: {target}")
    name_to_id = {str(k): str(v) for k, v in dict(params.get("name_to_id") or {}).items()}
    problems: list[str] = []
    for path in _suite_files(suite):
        for value, line in _arguments(path):
            problems.extend(f"{path.name}:{line}: {p}" for p in locator_problems(value, name_to_id))
    if problems:
        return Verdict.of(run.id, name, False, "; ".join(problems[:8]))
    return Verdict.of(run.id, name, True, "locators use @Id or a language-independent form")
