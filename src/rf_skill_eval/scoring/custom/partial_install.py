"""Grader for partial-install tasks (skill-eval-harness "Partial-install tier").

With only ``rf-core`` staged, a task about one technology passes when the agent
names that technology's plugin as the thing to install, or when what it
produced still passes the task's gating check. It fails when the agent writes
library code from memory that fails the check.

    - type: custom_python
      name: suggests_plugin_or_passes
      func_ref: rf_skill_eval.scoring.custom.partial_install:suggests_plugin_or_passes
      plugin: rf-web
      check: {type: robot_pass, target: tests/login.robot, requires: [Browser], expected_tests: 1}
"""

from __future__ import annotations

import re
from typing import Any

from ...domain.run import Run
from ...domain.verdict import Verdict
from ...infrastructure.telemetry.session_parser import AssistantMessage, parse_session_jsonl
from ..deterministic import lookup_check

_INSTALL = re.compile(r"\binstall", re.IGNORECASE)


def assistant_text(run: Run) -> str:
    """Everything the agent said in the run."""
    if run.session_jsonl_path is None or not run.session_jsonl_path.is_file():
        return ""
    return "\n".join(e.text for e in parse_session_jsonl(run.session_jsonl_path) if isinstance(e, AssistantMessage))


def suggests_plugin(text: str, plugin: str) -> bool:
    """A sentence (or line) that names ``plugin`` and an install."""
    pattern = re.compile(rf"(?<![\w-]){re.escape(plugin)}(?![\w-])")
    return any(pattern.search(s) and _INSTALL.search(s) for s in re.split(r"(?<=[.!?])\s+|\n", text))


def suggests_plugin_or_passes(run: Run, params: dict[str, Any]) -> Verdict | dict[str, Any]:
    plugin = str(params.get("plugin") or "")
    if not plugin:
        return {"passed": False, "details": "custom check needs 'plugin'"}
    if suggests_plugin(assistant_text(run), plugin):
        return {"passed": True, "details": f"suggests installing {plugin}"}
    check = dict(params.get("check") or {})
    kind = str(check.pop("type", ""))
    # Same alias the rubric grader applies to top-level checks.
    if "path" not in check and "target" in check:
        check["path"] = check["target"]
    if not kind:
        return {"passed": False, "details": f"does not suggest installing {plugin}"}
    inner = lookup_check(kind)(run, f"{kind} (instead of suggesting {plugin})", check)
    detail = f"does not suggest installing {plugin}; {kind}: {inner.status}"
    if inner.details:
        detail += f" ({inner.details})"
    return {"passed": inner.status == "passed", "details": detail}
