"""Tier evidence (spec plugin-trust-tiers; change lean-governance, design D4)."""
from __future__ import annotations

import datetime as dt
import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


gov = _load("check_governance", "check-governance.py")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for cat in (ROOT / "plugins").glob("*/catalog.yaml"):
        shutil.copytree(cat.parent, tmp_path / "plugins" / cat.parent.name,
                        ignore=shutil.ignore_patterns("tests", "variants", "__pycache__"))
    return tmp_path


def test_repository_passes(capsys) -> None:
    assert gov.main([]) == 0
    out = capsys.readouterr().out
    assert out.strip() == "governance: tier evidence OK"


def test_verified_without_evals_is_refused(repo: Path) -> None:
    shutil.rmtree(repo / "plugins" / "rf-mobile" / "evals" / "triggers")
    assert gov.tier_problems(repo) == ["rf-mobile (verified): trigger-sets: no trigger set for rf-appium"]


def test_one_maintainer_is_enough(repo: Path) -> None:
    cat = repo / "plugins" / "rf-web" / "catalog.yaml"
    data = gov.catalogs(repo)["rf-web"]
    assert data["tier"] == "verified" and len(data["maintainers"]) == 1, cat
    assert gov.tier_problems(repo) == []


def test_same_tree_later_date(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    before = gov.tier_problems(repo)

    class Later(dt.date):
        @classmethod
        def today(cls) -> dt.date:
            return cls(2027, 2, 1)

    monkeypatch.setattr(dt, "date", Later)
    assert dt.date.today() == dt.date(2027, 2, 1)
    assert gov.tier_problems(repo) == before


def test_no_dated_exceptions_in_the_repository() -> None:
    assert not (ROOT / ".github" / "governance.yaml").exists()
    assert "tier_grace" not in (ROOT / "scripts" / "check-governance.py").read_text(encoding="utf-8")
