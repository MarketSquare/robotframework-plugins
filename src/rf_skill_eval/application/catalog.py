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
TIERS = ("narrow", "realistic", "adversarial", "partial")


def find_repo_root(start: Path | None = None) -> Path:
    """Nearest ancestor containing ``plugins/`` and ``eval/`` (else cwd)."""
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "plugins").is_dir() and (candidate / "eval").is_dir():
            return candidate
    return here


def shipped_skills(repo_root: Path, plugin: str | None = None) -> dict[str, str]:
    """``{skill name: dir name}`` for every ``plugins/*/skills/*/SKILL.md``
    (only ``plugins/<plugin>/skills/`` when ``plugin`` is given and not ``all``)."""
    found: dict[str, str] = {}
    pattern = "*" if plugin in (None, ALL_PLUGINS) else plugin
    for skills_dir in sorted((repo_root / "plugins").glob(f"{pattern}/skills")):
        found.update(skill_dir_map(skills_dir))
    return found


def eval_plugins(repo_root: Path) -> list[str]:
    """Plugins that carry their own evals (``plugins/<name>/evals/``)."""
    return sorted(p.parent.name for p in (repo_root / "plugins").glob("*/evals") if p.is_dir())


def default_eval_plugin(repo_root: Path) -> str:
    """The plugin the harness evaluates when ``--plugin`` is not given: the
    only plugin with evals. With several, the caller must choose (or ``all``)."""
    plugins = eval_plugins(repo_root)
    if len(plugins) != 1:
        found = ", ".join(plugins) or "none"
        raise ValueError(f"choose a plugin with --plugin, or --plugin all (plugins with evals: {found})")
    return plugins[0]


#: ``--plugin all``: every plugin's evals at once, read-only (see :func:`merged_evals_dir`).
ALL_PLUGINS = "all"
#: The plugin every technology plugin depends on; a partial-install task stages only it.
CORE_PLUGIN = "rf-core"


def plugin_evals_dir(repo_root: Path, plugin: str) -> Path:
    """``plugins/<plugin>/evals/``: the plugin's tasks, trigger sets and baselines.

    For ``all``, a merged copy of every plugin's evals (:func:`merged_evals_dir`)."""
    if plugin == ALL_PLUGINS:
        return merged_evals_dir(repo_root)
    return repo_root / "plugins" / plugin / "evals"


def _merge_baseline(files: list[Path]) -> dict[str, Any]:
    """One baseline from several plugins' files of the same kind: ``entries``
    (tiers) or ``skills`` (triggers) are joined; other keys come from the first."""
    merged: dict[str, Any] = {}
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        for key, value in data.items():
            if key in ("entries", "skills") and isinstance(value, dict):
                merged.setdefault(key, {}).update(value)
            else:
                merged.setdefault(key, value)
    return merged


_MERGED: dict[Path, Path] = {}


def merged_evals_dir(repo_root: Path) -> Path:
    """A temporary ``evals/`` holding every plugin's tasks, trigger sets and
    baselines, built once per process. Writing to it changes no plugin; commands
    that write baselines need one ``--plugin``."""
    root = repo_root.resolve()
    if root in _MERGED:
        return _MERGED[root]
    import atexit
    import shutil
    import tempfile

    out = Path(tempfile.mkdtemp(prefix="rf-eval-all-")) / "evals"
    atexit.register(shutil.rmtree, out.parent, ignore_errors=True)
    baselines: dict[str, list[Path]] = {}
    for plugin in eval_plugins(root):
        src = plugin_evals_dir(root, plugin)
        for f in sorted(src.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(src)
            if rel.parts[0] == "baselines" and f.suffix == ".json":
                baselines.setdefault(rel.name, []).append(f)
                continue
            dst = out / rel
            if dst.exists():
                if rel.suffix == ".md":
                    continue  # one README per folder is enough
                raise ValueError(f"{rel.as_posix()} exists in more than one plugin's evals")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst)
    for name, files in baselines.items():
        dst = out / "baselines" / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(_merge_baseline(files), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "tasks").mkdir(parents=True, exist_ok=True)
    (out / "triggers").mkdir(parents=True, exist_ok=True)
    _MERGED[root] = out
    return out


def _read_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    loaded = yaml.safe_load(text) if path.suffix.lower() in (".yaml", ".yml") else json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a mapping")
    return loaded


#: Run-time settings a task file may not declare (openrouter-ci-eval-tier).
_RUNTIME_ONLY_KEYS: tuple[str, ...] = ("turns_factor", "provider")


def load_task_file(path: Path) -> Task:
    data = _read_mapping(path)
    for key in _RUNTIME_ONLY_KEYS:
        if key in data:
            raise ValueError(f"'{key}' is a run-time setting and may not appear in a task file")
    return Task.model_validate(data)


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
    if task.tier == "partial" and not task.stage:
        problems.append(f"{path}: a partial task needs 'stage' (the plugins to stage, e.g. [rf-core])")
    if task.stage and fixtures_root is not None:
        from .staging import content_plugins

        known = content_plugins(fixtures_root.parent.parent / "plugins")
        unknown = [n for n in task.stage if n not in known]
        if unknown and known:
            problems.append(f"{path}: stage names unknown plugin(s) {unknown} (known: {known})")
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


def partial_problems(
    repo_root: Path, tasks: dict[str, tuple[Path, Task]], plugin: str | None = None
) -> list[str]:
    """Every technology plugin needs a partial-install task: one of its skills,
    run with only ``rf-core`` staged (skill-eval-harness "Partial-install tier")."""
    owner = {s: p.parent.name for p in sorted((repo_root / "plugins").glob("*/skills"))
             for s in skill_dir_map(p)}
    technology = sorted({p for p in owner.values() if p != CORE_PLUGIN})
    if plugin not in (None, ALL_PLUGINS):
        technology = [p for p in technology if p == plugin]
    covered = {owner.get(t.skill) for _p, t in tasks.values()
               if t.tier == "partial" and tuple(t.stage) == (CORE_PLUGIN,)}
    return [f"technology plugin '{p}' has no partial-install task (tier partial, stage [{CORE_PLUGIN}])"
            for p in technology if p not in covered]


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
    problems += partial_problems(repo_root, validation.tasks, plugin)
    return CoverageReport(
        skills=sorted(skills),
        narrow_tasks=narrow,
        trigger_sets=sorted(sets),
        problems=problems,
    )
