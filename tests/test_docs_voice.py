"""Docs voice check (spec programme-documentation; launch task 9.1)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("check_docs_voice", ROOT / "scripts" / "check-docs-voice.py")
voice = importlib.util.module_from_spec(_spec)
sys.modules["check_docs_voice"] = voice
_spec.loader.exec_module(voice)


def _doc(tmp_path: Path, text: str, name: str = "README.md") -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_banned_phrase(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Scenario: a PR adds "Our mission is to empower testers" to README.md."""
    doc = _doc(tmp_path, "# Plugins\n\nInstall them per agent.\n\nOur mission is to empower testers.\n")
    assert voice.main(["--root", str(tmp_path), str(doc)]) == 1
    assert capsys.readouterr().out.strip() == 'README.md:5: banned phrase "Our mission is"'


@pytest.mark.parametrize("phrase", ["leverages the API", "a Seamless install", "best in class", "World-class tests"])
def test_other_banned_phrases(phrase: str, tmp_path: Path) -> None:
    assert voice.check(_doc(tmp_path, f"# X\n\nIt {phrase}.\n"), tmp_path)


def test_one_exclamation_mark_is_fine_two_are_not(tmp_path: Path) -> None:
    assert voice.check(_doc(tmp_path, "# X\n\nIt works!\n"), tmp_path) == []
    (problem,) = voice.check(_doc(tmp_path, "# X\n\nIt works!\n\nReally!\n"), tmp_path)
    assert problem == "README.md: 2 exclamation marks (lines 3, 5); at most one per document"


def test_code_links_and_images_are_not_prose(tmp_path: Path) -> None:
    text = ("# X\n\n![logo](img.png) Run `seamless --leverage` first!\n\n```bash\nfoo != bar!\necho hi!\n```\n\n"
            "See [the guide](https://example.invalid/world-class).\n<!-- our mission is: nothing -->\n")
    assert voice.check(_doc(tmp_path, text), tmp_path) == []


def test_changelogs_and_dated_records_are_history(tmp_path: Path) -> None:
    _doc(tmp_path, "# Changes\n\nSeamless!!\n", "CHANGELOG.md")
    _doc(tmp_path, "# Report\n\n**Date:** 2026-03-17\n\nSeamless.\n", "docs/old-report.md")
    _doc(tmp_path, "# Catalogue\n\nPlain words.\n", "docs/catalog.md")
    assert [p.relative_to(tmp_path).as_posix() for p in voice.documents(tmp_path)] == ["docs/catalog.md"]


def test_repository_passes() -> None:
    assert [p for f in voice.documents(ROOT) for p in voice.check(f, ROOT)] == []
