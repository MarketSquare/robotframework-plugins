"""Loading and validating the eval content: shipped skills, tasks, trigger sets.

Validity rules (design D8, spec "Task coverage per shipped skill"):

* a task's ``skill`` is ``plugin`` (bundle canary) or the ``name`` of a skill
  under ``plugins/*/skills/*/SKILL.md`` — retired skills are rejected;
* the model follows the allow-list / YAML policy (enforced by the model);
* the fixture exists; ids are unique; the tier matches the tier directory;
* every task has at least one gating check;
* a task that allows ``mcp__rf-mcp__*`` tools declares ``mcp_servers: [rf-mcp]``.

Coverage: every skill a plugin ships needs at least one ``narrow`` task and one
trigger set in that plugin's ``evals/``. New skills are picked up automatically
from ``plugins/<name>/skills/``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from ..domain.task import PLUGIN_SKILL, Task
from ..domain.trigger import TriggerSet
from ..infrastructure.telemetry.skill_loads import skill_dir_map

TASK_SUFFIXES = (".yaml", ".yml", ".json")
TIERS = ("narrow", "realistic", "adversarial")


def find_repo_root(start: Path | None = None) -> Path:
    """Nearest ancestor containing ``plugins/`` and ``eval/`` (else cwd)."""
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "plugins").is_dir() and (candidate / "eval").is_dir():
            return candidate
    return here


def shipped_skills(repo_root: Path, plugin: str | None = None) -> dict[str, str]:
    """``{skill name: dir name}`` for every ``plugins/*/skills/*/SKILL.md``
    (only ``plugins/<plugin>/skills/`` when ``plugin`` is given)."""
    found: dict[str, str] = {}
    for skills_dir in sorted((repo_root / "plugins").glob(f"{plugin or '*'}/skills")):
        found.update(skill_dir_map(skills_dir))
    return found


def eval_plugins(repo_root: Path) -> list[str]:
    """Plugins that carry their own evals (``plugins/<name>/evals/``)."""
    return sorted(p.parent.name for p in (repo_root / "plugins").glob("*/evals") if p.is_dir())


def default_eval_plugin(repo_root: Path) -> str:
    """The plugin the harness evaluates when ``--plugin`` is not given: the
    only plugin with evals. With several, the caller must choose."""
    plugins = eval_plugins(repo_root)
    if len(plugins) != 1:
        found = ", ".join(plugins) or "none"
        raise ValueError(f"choose a plugin with --plugin (plugins with evals: {found})")
    return plugins[0]


def plugin_evals_dir(repo_root: Path, plugin: str) -> Path:
    """``plugins/<plugin>/evals/``: the plugin's tasks, trigger sets and baselines."""
    return repo_root / "plugins" / plugin / "evals"


def _read_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    loaded = yaml.safe_load(text) if path.suffix.lower() in (".yaml", ".yml") else json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a mapping")
    return loaded


def load_task_file(path: Path) -> Task:
    return Task.model_validate(_read_mapping(path))


def task_files(tasks_dir: Path) -> list[Path]:
    return sorted(p for p in tasks_dir.rglob("*") if p.suffix.lower() in TASK_SUFFIXES)


@dataclass
class ValidationReport:
    tasks: dict[str, tuple[Path, Task]] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def _short_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return "; ".join(
            f"{'.'.join(str(x) for x in e['loc']) or 'root'}: {e['msg']}" for e in exc.errors()
        )
    return f"{type(exc).__name__}: {exc}"


def task_problems(
    task: Task,
    path: Path,
    *,
    skills: dict[str, str],
    fixtures_root: Path | None,
) -> list[str]:
    problems: list[str] = []
    if task.skill != PLUGIN_SKILL and task.skill not in skills:
        problems.append(
            f"{path}: unknown skill '{task.skill}' (not a shipped skill; "
            f"known: {sorted(skills)} or '{PLUGIN_SKILL}')"
        )
    if task.fixture and fixtures_root is not None and not (fixtures_root / task.fixture).is_dir():
        problems.append(f"{path}: fixture '{task.fixture}' not found under {fixtures_root}")
    if not task.gating_checks:
        problems.append(
            f"{path}: no gating check (set primary_metric to a check type or mark a check "
            "gating: true)"
        )
    if any(t.startswith("mcp__rf-mcp__") for t in task.allowed_tools) and (
        "rf-mcp" not in task.mcp_servers
    ):
        problems.append(f"{path}: allows mcp__rf-mcp__* tools but does not declare mcp_servers: [rf-mcp]")
    tier_dir = next((part for part in path.parts if part in TIERS), None)
    if tier_dir is not None and tier_dir != task.tier:
        problems.append(f"{path}: tier '{task.tier}' does not match directory '{tier_dir}/'")
    return problems


def validate_tasks(
    tasks_dir: Path,
    *,
    skills: dict[str, str],
    fixtures_root: Path | None = None,
) -> ValidationReport:
    report = ValidationReport()
    files = task_files(tasks_dir)
    if not files:
        report.problems.append(f"{tasks_dir}: no task files found")
    for path in files:
        try:
            task = load_task_file(path)
        except Exception as exc:
            report.problems.append(f"{path}: {_short_error(exc)}")
            continue
        if task.id in report.tasks:
            report.problems.append(
                f"{path}: duplicate task id '{task.id}' (also {report.tasks[task.id][0]})"
            )
            continue
        report.tasks[task.id] = (path, task)
        report.problems.extend(
            task_problems(task, path, skills=skills, fixtures_root=fixtures_root)
        )
    return report


def load_trigger_set(path: Path, *, skills: dict[str, str] | None = None) -> TriggerSet:
    """Load and validate one trigger set; errors name the set and the problem."""
    try:
        tset = TriggerSet.model_validate(_read_mapping(path))
    except Exception as exc:
        raise ValueError(f"trigger set {path}: {_short_error(exc)}") from exc
    if skills is not None and tset.skill not in skills:
        raise ValueError(
            f"trigger set {path}: unknown skill '{tset.skill}' (known: {sorted(skills)})"
        )
    if path.stem != tset.skill:
        raise ValueError(f"trigger set {path}: file name must be '{tset.skill}.yaml'")
    return tset


def load_trigger_sets(
    triggers_dir: Path, *, skills: dict[str, str] | None = None
) -> tuple[dict[str, TriggerSet], list[str]]:
    sets: dict[str, TriggerSet] = {}
    problems: list[str] = []
    if not triggers_dir.is_dir():
        return sets, [f"{triggers_dir}: trigger directory missing"]
    for path in sorted(triggers_dir.glob("*.y*ml")):
        try:
            tset = load_trigger_set(path, skills=skills)
        except ValueError as exc:
            problems.append(str(exc))
            continue
        sets[tset.skill] = tset
    return sets, problems


@dataclass
class CoverageReport:
    skills: list[str]
    narrow_tasks: dict[str, list[str]]
    trigger_sets: list[str]
    problems: list[str]

    @property
    def ok(self) -> bool:
        return not self.problems


def coverage(
    repo_root: Path, tasks_dir: Path, triggers_dir: Path, plugin: str | None = None
) -> CoverageReport:
    skills = shipped_skills(repo_root, plugin)
    validation = validate_tasks(tasks_dir, skills=skills, fixtures_root=repo_root / "eval" / "fixtures")
    sets, trigger_problems = load_trigger_sets(triggers_dir, skills=skills)
    narrow: dict[str, list[str]] = {name: [] for name in skills}
    for task_id, (_path, task) in sorted(validation.tasks.items()):
        if task.tier == "narrow" and task.skill in narrow:
            narrow[task.skill].append(task_id)
    problems = list(validation.problems) + trigger_problems
    for name in sorted(skills):
        if not narrow[name]:
            problems.append(f"skill '{name}' has no narrow task under {tasks_dir}")
        if name not in sets:
            problems.append(f"skill '{name}' has no trigger set ({triggers_dir}/{name}.yaml)")
    return CoverageReport(
        skills=sorted(skills),
        narrow_tasks=narrow,
        trigger_sets=sorted(sets),
        problems=problems,
    )
