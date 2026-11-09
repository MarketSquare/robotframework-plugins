"""Baseline comparison of scanner findings (spec content-security-scanning,
"The gate fails on new findings only"; design D8)."""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("compare_findings", ROOT / "scripts" / "compare-findings.py")
cf = importlib.util.module_from_spec(_spec)
sys.modules["compare_findings"] = cf
_spec.loader.exec_module(cf)

TODAY = dt.date(2026, 11, 9)
REF = "plugins/rf-core/skills/rf-setup/references/troubleshooting.md"


def _result(rule: str, uri: str, severity: str, finding: str, line: int = 10) -> dict:
    return {"ruleId": rule, "level": "error" if severity in ("HIGH", "CRITICAL") else "warning",
            "message": {"text": rule}, "properties": {"severity": severity, "finding": finding},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": uri}, "region": {"startLine": line}}}]}


def _sarif(tmp_path: Path, *results: dict, name: str = "ss.sarif") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps({"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "x"}}, "results": list(results)}]}))
    return path


def _entry(finding: cf.Finding, **over: object) -> dict:
    entry = {"scanner": finding.scanner, "rule": finding.rule, "file": finding.file,
             "fingerprint": finding.fingerprint, "reason": "Documents what not to do.",
             "reviewed_by": "security-team", "expires": "2027-06-30"}
    entry.update(over)
    return entry


def _baseline(tmp_path: Path, *entries: dict) -> Path:
    path = tmp_path / "rf-core.yaml"
    path.write_text(yaml.safe_dump({"plugin": "rf-core", "entries": list(entries)}))
    return path


def _sudo_pip(tmp_path: Path) -> tuple[Path, cf.Finding]:
    sarif = _sarif(tmp_path, _result("PE2", "skills/rf-setup/references/troubleshooting.md", "HIGH",
                                     "sudo pip install"))
    (finding,) = cf.read_sarif("skillspector", sarif, "plugins/rf-core")
    return sarif, finding


def test_known_false_positive_does_not_fail(tmp_path: Path) -> None:
    sarif, finding = _sudo_pip(tmp_path)
    assert finding.file == REF
    baseline = _baseline(tmp_path, _entry(finding))
    out = tmp_path / "summary.md"
    code = cf.main(["--baseline", str(baseline), "--sarif", f"skillspector={sarif}@plugins/rf-core",
                    "--summary", str(out), "--today", TODAY.isoformat()])
    assert code == 0
    text = out.read_text()
    assert "rf-core, passed" in text and "### Accepted findings" in text and "Documents what not to do." in text


def test_expired_baseline_entry(tmp_path: Path) -> None:
    sarif, finding = _sudo_pip(tmp_path)
    baseline = _baseline(tmp_path, _entry(finding, expires="2026-11-08"))
    out = tmp_path / "summary.md"
    code = cf.main(["--baseline", str(baseline), "--sarif", f"skillspector={sarif}@plugins/rf-core",
                    "--summary", str(out), "--today", TODAY.isoformat()])
    assert code == 1
    assert "expired on 2026-11-08" in out.read_text()


def test_new_high_fails_and_medium_is_only_reported(tmp_path: Path) -> None:
    high = _sarif(tmp_path, _result("EX1", "plugins/rf-core/scripts/hook.mjs", "HIGH", "fetch(env)"), name="h.sarif")
    medium = _sarif(tmp_path, _result("ST1", "plugins/rf-core/scripts/hook.mjs", "MEDIUM", "x"), name="m.sarif")
    base = _baseline(tmp_path)
    assert cf.main(["--baseline", str(base), "--sarif", f"cisco={high}", "--today", TODAY.isoformat()]) == 1
    assert cf.main(["--baseline", str(base), "--sarif", f"cisco={medium}", "--today", TODAY.isoformat()]) == 0


def test_critical_from_the_sarif_level(tmp_path: Path) -> None:
    result = _result("X", "plugins/rf-core/scripts/a.py", "", "y")
    result["properties"].pop("severity")
    result["level"] = "error"
    (finding,) = cf.read_sarif("cisco", _sarif(tmp_path, result))
    assert finding.severity == "HIGH"


@pytest.mark.parametrize(
    ("over", "problem"),
    [({"expires": "2028-01-01"}, "more than 12 months away"), ({"reason": ""}, "missing reason"),
     ({"reviewed_by": None}, "missing reviewed_by"), ({"expires": "soon"}, "not a date")],
)
def test_invalid_baseline_entries_fail(over: dict, problem: str, tmp_path: Path) -> None:
    _, finding = _sudo_pip(tmp_path)
    res = cf.compare([finding], [_entry(finding, **over)], TODAY)
    assert not res.ok and problem in res.invalid[0][1]


def test_fingerprint_ignores_line_moves(tmp_path: Path) -> None:
    a = cf.read_sarif("s", _sarif(tmp_path, _result("R", "f.md", "HIGH", "same text", line=3), name="a.sarif"))
    b = cf.read_sarif("s", _sarif(tmp_path, _result("R", "f.md", "HIGH", "same   text", line=40), name="b.sarif"))
    c = cf.read_sarif("s", _sarif(tmp_path, _result("R", "f.md", "HIGH", "other text", line=3), name="c.sarif"))
    assert a[0].fingerprint == b[0].fingerprint != c[0].fingerprint


@pytest.mark.parametrize(
    ("uri", "base", "want"),
    [("agents/a.md", "plugins/rf-core", "plugins/rf-core/agents/a.md"),
     ("plugins/rf-core/agents/a.md", "plugins/rf-core", "plugins/rf-core/agents/a.md"),
     ("./skills/x/SKILL.md", "plugins/rf-web", "plugins/rf-web/skills/x/SKILL.md"),
     ("plugins/rf-web/skills/x/SKILL.md", "", "plugins/rf-web/skills/x/SKILL.md")],
)
def test_paths_are_repository_relative(uri: str, base: str, want: str) -> None:
    assert cf._path(uri, base) == want


def test_draft_lists_new_findings_for_review(tmp_path: Path) -> None:
    sarif, finding = _sudo_pip(tmp_path)
    draft = tmp_path / "draft.yaml"
    cf.main(["--baseline", str(tmp_path / "none.yaml"), "--plugin", "rf-core",
             "--sarif", f"skillspector={sarif}@plugins/rf-core", "--draft", str(draft), "--today", TODAY.isoformat()])
    data = yaml.safe_load(draft.read_text())
    assert data["plugin"] == "rf-core"
    (entry,) = data["entries"]
    assert entry["fingerprint"] == finding.fingerprint and entry["reason"] == ""


def test_unused_entries_are_reported(tmp_path: Path) -> None:
    _, finding = _sudo_pip(tmp_path)
    res = cf.compare([], [_entry(finding)], TODAY)
    assert res.ok and len(res.unused) == 1
    assert "can be removed" in cf.summary(res, "rf-core")


def test_empty_sarif_file(tmp_path: Path) -> None:
    empty = tmp_path / "e.sarif"
    empty.write_text("")
    assert cf.read_sarif("cc-audit", empty) == []


def test_bundle_copy_is_judged_by_the_source_plugins_baseline(tmp_path: Path) -> None:
    """A finding in bundles/rf-agentskills/ matches the entry for the file it
    was copied from (design D15: generated copies have one owner)."""
    src = cf.read_sarif("skillspector", _sarif(tmp_path, _result("PE2", REF, "HIGH", "sudo pip install"), name="s.sarif"))
    copy = REF.replace("plugins/rf-core/", "bundles/rf-agentskills/")
    bundle = cf.read_sarif("skillspector", _sarif(tmp_path, _result("PE2", copy, "HIGH", "sudo pip install"), name="b.sarif"))
    assert src[0].fingerprint == bundle[0].fingerprint
    baseline = _baseline(tmp_path, _entry(src[0]))
    sarif = tmp_path / "b.sarif"
    args = ["--baseline", str(baseline), "--sarif", f"skillspector={sarif}", "--today", TODAY.isoformat()]
    assert cf.main(args) == 1
    assert cf.main([*args, "--map", "plugins/rf-core/=bundles/rf-agentskills/"]) == 0
