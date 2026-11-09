"""Quarterly adoption report on fixture data (spec adoption-reporting; launch task 8.2)."""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("adoption_report", ROOT / "scripts" / "adoption-report.py")
ar = importlib.util.module_from_spec(_spec)
sys.modules["adoption_report"] = ar
_spec.loader.exec_module(ar)


def _feedback(number: int, plugin: str, helped: str, created: str = "2026-11-02T10:00:00Z") -> dict:
    body = f"### Plugin\n\n{plugin}\n\n### Did the plugin help?\n\n{helped}\n\n### What happened\n\nx\n"
    return {"number": number, "state": "closed", "labels": [{"name": "feedback"}, {"name": f"plugin:{plugin}"}],
            "created_at": created, "body": body}


@pytest.fixture
def data(tmp_path: Path) -> Path:
    d = tmp_path / "data"
    for snap, days in (("2026-10-12", range(1, 13)), ("2026-10-19", range(6, 20))):
        (d / "traffic" / snap).mkdir(parents=True)
        for kind in ("views", "clones"):
            rows = [{"timestamp": f"2026-10-{day:02d}T00:00:00Z", "count": 10, "uniques": 3} for day in days]
            (d / "traffic" / snap / f"{kind}.json").write_text(json.dumps({kind: rows}))
    (d / "pypi.json").write_text(json.dumps({"data": [
        {"category": "without_mirrors", "date": "2026-10-05", "downloads": 40},
        {"category": "with_mirrors", "date": "2026-10-05", "downloads": 90},
        {"category": "without_mirrors", "date": "2026-09-30", "downloads": 500}]}))
    (d / "issues.json").write_text(json.dumps([
        _feedback(1, "rf-core", "Yes"), _feedback(2, "rf-core", "Partly"), _feedback(3, "rf-web", "No"),
        _feedback(4, "rf-core", "Yes", created="2026-08-01T00:00:00Z"),
        {"number": 5, "state": "open", "labels": ["plugin:rf-web"], "created_at": "2026-10-03T00:00:00Z", "body": ""},
    ]))
    (d / "evals.json").write_text(json.dumps({
        "rf-web": [{"release": "1.0.0", "date": "2026-09-01", "score": 1.0},
                   {"release": "1.1.0", "date": "2026-10-01", "score": 0.94},
                   {"release": "1.2.0", "date": "2026-11-01", "score": 0.89}],
        "rf-core": [{"release": "1.0.0", "date": "2026-09-01", "score": 0.97},
                    {"release": "1.1.0", "date": "2026-10-01", "score": 1.0}],
    }))
    return d


def test_report_on_fixture_data(data: Path, tmp_path: Path) -> None:
    out = tmp_path / "docs" / "reports" / "adoption-2026-Q4.md"
    assert ar.main(["--data", str(data), "--quarter", "2026-Q4", "--output", str(out)]) == 0
    text = out.read_text()
    assert text.startswith("# Adoption report 2026-Q4\n\n2026-10-01 to 2026-12-31.")
    # Overlapping snapshots: days 1-19 counted once each.
    assert "| GitHub views | 190 (19 of 92 days recorded) |" in text
    assert "| PyPI downloads of robotframework-plugins | 40 |" in text
    assert "| `rf-core` | verified | active | 1 | 1 | 0 | 0 | 100% | up 3% |" in text
    assert "| `rf-web` | verified | active | 0 | 0 | 1 | 1 | 89% | down 5% |" in text


def test_report_names_candidates(data: Path) -> None:
    text = ar.render("2026-Q4", ROOT, data, json.loads((data / "evals.json").read_text()))
    assert "**Demotion:** `rf-web`, eval score fell for two releases (100% → 94% → 89%)." in text
    assert "**Promotion:** none." in text


def test_promotion_and_deprecation_rules() -> None:
    cats = {"rf-db": {"tier": "community", "status": "active", "maintainers": [{"github": "a"}, {"github": "b"}]},
            "rf-old": {"tier": "community", "status": "active", "maintainers": [{"github": "c"}]},
            "rf-orphan": {"tier": "community", "status": "active", "maintainers": []}}
    evals = {"rf-db": [{"score": 0.9}], "rf-old": [{"score": 0.4}]}
    found = ar.candidates(cats, evals, {"rf-db": {"Yes": 2, "No": 1}})
    assert [n for n, _ in found["promotion"]] == ["rf-db"]
    assert [n for n, _ in found["deprecation"]] == ["rf-old", "rf-orphan"]


def test_quarter_range() -> None:
    assert ar.quarter_range("2026-Q4") == (dt.date(2026, 10, 1), dt.date(2026, 12, 31))
    assert ar.quarter_range("2027-Q1") == (dt.date(2027, 1, 1), dt.date(2027, 3, 31))


def test_narrow_score_of_the_committed_baselines() -> None:
    baseline = json.loads((ROOT / "plugins" / "rf-core" / "evals" / "baselines" / "narrow.json").read_text())
    assert 0.0 < ar.narrow_score(baseline) <= 1.0


def test_feedback_form_lists_every_listed_plugin() -> None:
    form = yaml.safe_load((ROOT / ".github" / "ISSUE_TEMPLATE" / "plugin-feedback.yml").read_text())
    plugin = next(b for b in form["body"] if b.get("id") == "plugin")
    listed = sorted(n for n, c in ar.catalogs(ROOT).items() if c.get("status") in ("active", "deprecated"))
    assert plugin["attributes"]["options"] == listed
    helped = next(b for b in form["body"] if b.get("id") == "helped")
    assert helped["attributes"]["label"] == "Did the plugin help?"
    assert "feedback" in form["labels"]
