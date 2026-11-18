"""The one release workflow (spec release-train; single-release-version D2, D3)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"

_spec = importlib.util.spec_from_file_location("build_catalog_release", ROOT / "scripts" / "build-catalog.py")
bc = importlib.util.module_from_spec(_spec)
sys.modules["build_catalog_release"] = bc
_spec.loader.exec_module(bc)


@pytest.fixture(scope="module")
def wf() -> dict:
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    data["on"] = data.pop(True, data.get("on"))  # YAML 1.1 reads the key `on` as True
    return data


def _needs(job: dict) -> list[str]:
    needs = job.get("needs", [])
    return [needs] if isinstance(needs, str) else list(needs)


def test_only_release_tags_trigger(wf: dict) -> None:
    assert wf["on"] == {"push": {"tags": ["v[0-9]*"]}}


def test_tag_checks_come_before_any_build(wf: dict) -> None:
    jobs = wf["jobs"]
    check = jobs["check"]
    assert _needs(check) == []
    script = "\n".join(step.get("run", "") for step in check["steps"])
    assert "(3, 0, 0)" in script and "installer/pyproject.toml" in script and "plugin.json" in script
    assert not any("tar " in step.get("run", "") or "build" in step.get("run", "") for step in check["steps"])
    assert _needs(jobs["ci"]) == ["check"]


def test_job_order(wf: dict) -> None:
    jobs = wf["jobs"]
    assert list(jobs) == ["check", "ci", "release", "publish", "update-branches"]
    assert set(_needs(jobs["release"])) == {"check", "ci"}
    assert "release" in _needs(jobs["publish"])
    assert "publish" in _needs(jobs["update-branches"])


def test_candidates(wf: dict) -> None:
    jobs = wf["jobs"]
    assert jobs["update-branches"]["if"] == "needs.check.outputs.candidate != 'yes'"
    assert "testpypi" in jobs["publish"]["environment"]["name"]
    release = next(s for s in jobs["release"]["steps"] if s.get("name") == "Create the GitHub release")
    assert release["with"]["prerelease"] == "${{ needs.check.outputs.candidate == 'yes' }}"


def test_nothing_from_the_old_scheme() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    body = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    assert "bundles/" not in body and "--v" not in body
    assert "date -u" not in body and "month" not in body


SAMPLE = """# Changelog

## Unreleased

## 5.1.0 — 2026-12-02

### rf-web
- Newer.

## 5.0.0 — 2026-11-20

### Breaking
- The bundle is gone.

### rf-core
- A change.

## History before one version

### rf-core

#### 5.0.0 (made up, never matched)
- Old.
"""


def test_release_notes_hold_exactly_the_section(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text(SAMPLE, encoding="utf-8")
    assert bc.changelog_section(tmp_path, "5.0.0") == "### Breaking\n- The bundle is gone.\n\n### rf-core\n- A change."
    assert bc.changelog_section(tmp_path, "5.1.0") == "### rf-web\n- Newer."
    with pytest.raises(bc.CatalogError):
        bc.changelog_section(tmp_path, "4.0.0")


def test_release_notes_of_the_repository(capsys: pytest.CaptureFixture[str]) -> None:
    """The notes CI writes for the current version: install lines, its section, the plugins."""
    version = bc.installer_version(ROOT)
    if not (ROOT / "CHANGELOG.md").is_file() or f"## {version} " not in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"):
        pytest.skip(f"CHANGELOG.md has no {version} section yet (it is written by bump-version.sh)")
    assert bc.main(["--release-notes", version]) == 0
    out = capsys.readouterr().out
    assert f"`v{version}`" in out and f"robotframework-plugins=={version}" in out
    assert "| `rf-core` | verified |" in out
