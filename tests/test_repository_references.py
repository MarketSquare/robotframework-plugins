"""The repository moved to MarketSquare/robotframework-plugins (repository-migration).

Tracked files must not point users at the old repository or the old
marketplace name, apart from the places that are history or that migrate
old settings on purpose.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

OLD = re.compile(r"manykarim/robotframework-agentskills|robotframework-agentskills")

#: History: planning and specs (main specs are rewritten when a change is
#: archived), changelogs, and the dated plans and reports under docs/.
EXEMPT_PREFIXES = ("openspec/", "docs/")
EXEMPT_NAMES = ("CHANGELOG.md",)
#: libdoc JSON generated on a developer machine; the match is a local path.
EXEMPT_GLOBS = ("eval/fixtures/*/specs/*.json",)
#: Migration notes: code and tests that recognise the old marketplace.
MIGRATION_NOTES = (
    "installer/src/robotframework_plugins/adapters/_base.py",
    "tests/installer/test_plugin_mode.py",
    "tests/test_repository_references.py",
)


def _tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO, check=True, capture_output=True
    ).stdout.decode()
    return [f for f in out.split("\0") if f]


def _exempt(path: str) -> bool:
    return (
        path.startswith(EXEMPT_PREFIXES)
        or Path(path).name in EXEMPT_NAMES
        or any(Path(path).match(g) for g in EXEMPT_GLOBS)
        or path in MIGRATION_NOTES
    )


def test_no_stale_repository_references() -> None:
    hits = []
    for rel in _tracked_files():
        if _exempt(rel):
            continue
        path = REPO / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if OLD.search(line):
                hits.append(f"{rel}:{n}: {line.strip()[:120]}")
    assert not hits, "old repository or marketplace named in:\n" + "\n".join(hits)


def test_migration_notes_still_name_the_old_marketplace() -> None:
    """The allow-list must not hide files that no longer need it."""
    for rel in MIGRATION_NOTES[:-1]:
        assert OLD.search((REPO / rel).read_text(encoding="utf-8")), f"{rel} no longer needs an exemption"
