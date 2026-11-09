"""Trigger accuracy with part of the plugins installed (split-rf-agentskills,
skill-triggering "Trigger accuracy holds for partial installs").

With ``trigger --stage rf-core,rf-web`` only those plugins' skills are staged.
The staged skills' sets are scored as usual. A should-trigger query of a
technology whose plugin is not staged cannot load its own skill; it counts as
correct when no staged skill of another technology loads (an API question must
not end in ``rf-browser``). Core skills don't count: they serve every technology.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from ..domain.trigger import QueryOutcome

CORE = "rf-core"


@dataclass(frozen=True)
class CrossTechnology:
    """Should-trigger queries of one unstaged plugin's skills."""

    plugin: str
    queries: int
    #: Queries in which a staged skill of another technology loaded.
    crossed: int
    #: Those staged skills, with the number of queries each loaded in.
    loaded: tuple[tuple[str, int], ...]

    @property
    def rate(self) -> float:
        return self.crossed / self.queries if self.queries else 0.0


def staged_skills(owner: Mapping[str, str], staged: Iterable[str]) -> set[str]:
    """Skills of the staged plugins (``owner`` maps skill -> plugin)."""
    plugins = set(staged)
    return {skill for skill, plugin in owner.items() if plugin in plugins}


def split_outcomes(
    outcomes: Iterable[QueryOutcome], staged: set[str]
) -> tuple[list[QueryOutcome], list[QueryOutcome]]:
    """(outcomes of staged skills' sets, outcomes of the other sets)."""
    on: list[QueryOutcome] = []
    off: list[QueryOutcome] = []
    for o in outcomes:
        (on if o.skill in staged else off).append(o)
    return on, off


def cross_technology(
    unstaged: Iterable[QueryOutcome], staged: set[str], owner: Mapping[str, str]
) -> list[CrossTechnology]:
    """Per unstaged plugin: how many of its should-trigger queries loaded a
    staged technology skill instead (``rf-core`` skills are not counted)."""
    technology = {s for s in staged if owner.get(s) != CORE}
    queries: Counter[str] = Counter()
    crossed: Counter[str] = Counter()
    loaded: dict[str, Counter[str]] = {}
    for o in unstaged:
        if not o.should_trigger or o.runs == 0:
            continue
        plugin = owner.get(o.skill, "?")
        queries[plugin] += 1
        hit = set(o.other_skills) & technology
        if hit:
            crossed[plugin] += 1
            loaded.setdefault(plugin, Counter()).update(hit)
    return [
        CrossTechnology(plugin=p, queries=queries[p], crossed=crossed[p],
                        loaded=tuple(sorted(loaded.get(p, Counter()).items())))
        for p in sorted(queries)
    ]


def cross_technology_json(rows: list[CrossTechnology], staged_plugins: Iterable[str]) -> dict[str, object]:
    return {
        "kind": "partial-install",
        "staged": sorted(staged_plugins),
        "cross_technology": {
            r.plugin: {"queries": r.queries, "crossed": r.crossed, "rate": round(r.rate, 4),
                       "loaded": dict(r.loaded)}
            for r in rows
        },
    }


def render_cross_technology(rows: list[CrossTechnology], staged_plugins: Iterable[str]) -> list[str]:
    staged = ", ".join(sorted(staged_plugins))
    out = [
        "",
        "## Partial install: technologies not staged",
        "",
        f"Staged: {staged}. A should-trigger query of an unstaged plugin is correct when no "
        "staged skill of another technology loads (core skills don't count).",
        "",
    ]
    if not rows:
        return [*out, "_No query of an unstaged plugin ran._"]
    out += ["| Queries of | Queries | Loaded a staged technology skill | Rate | Skills |", "|---|---|---|---|---|"]
    for r in rows:
        skills = ", ".join(f"{s} ({n})" for s, n in r.loaded) or "none"
        out.append(f"| {r.plugin} | {r.queries} | {r.crossed} | {r.rate:.0%} | {skills} |")
    return out
