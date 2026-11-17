"""The model-assisted scan's trigger and gating (spec content-security-scanning,
"Model-assisted scans run only after maintainer approval"; change
lean-governance, design D9)."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def _on(wf: dict) -> dict:
    on = wf.get("on", wf.get(True))
    return on if isinstance(on, dict) else {name: None for name in ([on] if isinstance(on, str) else on)}


def _steps() -> dict[str, dict]:
    wf = yaml.safe_load((WORKFLOWS / "security-deep-scan.yml").read_text(encoding="utf-8"))
    return {s.get("name", s.get("uses", "")): s for s in wf["jobs"]["deep-scan"]["steps"]}


def test_no_workflow_uses_pull_request_target() -> None:
    """GitHub blocks the event in public repositories from 2026-12-02, and it
    runs with secrets next to fork code."""
    for path in sorted(WORKFLOWS.glob("*.yml")):
        assert "pull_request_target" not in _on(yaml.safe_load(path.read_text(encoding="utf-8"))), path.name


def test_a_maintainer_starts_the_scan_by_pr_number() -> None:
    wf = yaml.safe_load((WORKFLOWS / "security-deep-scan.yml").read_text(encoding="utf-8"))
    on = _on(wf)
    assert set(on) == {"workflow_dispatch", "push"}
    assert on["push"] == {"branches": ["main"]}
    assert set(on["workflow_dispatch"]["inputs"]) == {"pr", "sha"}


def test_the_pr_is_data_only() -> None:
    steps = _steps()
    fetch = steps["Fetch the PR head as data"]["run"]
    assert "git init" in fetch and "refs/pull/$PR/head" in fetch
    assert "actions/checkout" not in str(steps["Fetch the PR head as data"])
    assert steps["Check out the trusted scripts"]["with"]["persist-credentials"] is False
    assert "REVIEWED_SHA" in steps["Look up the PR"]["run"]


def test_findings_fail_a_pr_scan_but_only_report_on_main() -> None:
    fail = _steps()["Fail on new findings in a PR, or on a broken scan"]["if"]
    assert fail == "steps.scan.outputs.status == 'broken' || (inputs.pr && steps.scan.outputs.status == 'findings')"
