"""Ownership, tier evidence and required reviews (spec plugin-trust-tiers;
design D9; launch tasks 6.2 and 6.3)."""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "required-reviews"


def _load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


gov = _load("check_governance", "check-governance.py")
rr = _load("required_reviews", "required-reviews.py")
TODAY = dt.date(2026, 11, 9)


def _snap(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def _groups(name: str) -> dict[str, rr.Group]:
    return {g.name: g for g in rr.required_groups(_snap(name), rr.governance(ROOT))}


# --- required reviews -------------------------------------------------------

def test_hook_change_needs_the_security_team() -> None:
    groups = _groups("hook-change-owner-only")
    assert set(groups) == {"owners:rf-core", "foundation", "security"}
    assert groups["owners:rf-core"].ok and groups["foundation"].ok and not groups["security"].ok
    assert rr.main([str(FIXTURES / "hook-change-owner-only.json")]) == 1
    assert rr.main([str(FIXTURES / "hook-change-with-security.json")]) == 0


def test_tier_promotion_needs_a_foundation_reviewer(capsys) -> None:
    groups = _groups("tier-promotion-maintainers-only")
    assert groups["foundation"].reasons == ["promotes rf-db to verified"]
    assert groups["owners:rf-db"].ok and not groups["foundation"].ok
    assert rr.main([str(FIXTURES / "tier-promotion-maintainers-only.json")]) == 1
    assert "@MarketSquare/robotframework-plugins-reviewers" in capsys.readouterr().out


def test_author_approval_and_stale_reviews_do_not_count() -> None:
    snap = _snap("hook-change-with-security")
    snap["author"] = "sec-1"
    snap["reviews"].append({"user": "maint-a", "state": "CHANGES_REQUESTED", "submitted_at": "2026-11-09T12:00:00Z"})
    groups = {g.name: g for g in rr.required_groups(snap, rr.governance(ROOT))}
    assert not groups["security"].ok  # the author's own approval
    assert not groups["owners:rf-core"].ok  # maint-a's latest review requests changes


def test_a_pr_cannot_add_its_author_as_maintainer() -> None:
    snap = _snap("tier-promotion-maintainers-only")
    snap["head_catalogs"]["rf-db"]["maintainers"].append({"github": "contrib"})
    snap["reviews"] = [{"user": "contrib", "state": "APPROVED", "submitted_at": "2026-11-09T10:00:00Z"}]
    assert not {g.name: g for g in rr.required_groups(snap, rr.governance(ROOT))}["owners:rf-db"].ok


def test_allowed_tools_change_in_a_skill_is_security_relevant() -> None:
    patterns = rr.governance(ROOT)["security_paths"]
    skill = "plugins/rf-web/skills/rf-browser/SKILL.md"
    assert rr.security_relevant({"filename": skill, "patch": "@@\n-allowed-tools: Read\n+allowed-tools: Read Bash"}, patterns)
    assert not rr.security_relevant({"filename": skill, "patch": "@@\n-Old text\n+New text"}, patterns)
    for path in ("plugins/rf-core/scripts/x.mjs", "plugins/rf-core/skills/rf-setup/scripts/a.py",
                 "security/baselines/rf-core.yaml", ".github/workflows/ci.yml", "plugins/rf-x/.mcp.json"):
        assert rr.security_relevant({"filename": path}, patterns), path
    assert not rr.security_relevant({"filename": "plugins/rf-web/skills/rf-browser/references/x.md"}, patterns)


def test_docs_only_change_needs_no_group() -> None:
    snap = {"author": "a", "files": [{"filename": "README.md"}], "reviews": [], "base_catalogs": {}, "head_catalogs": {}}
    assert rr.required_groups(snap, rr.governance(ROOT)) == []


# --- ownership and tier evidence -------------------------------------------

@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for rel in (".github/CODEOWNERS", ".github/governance.yaml"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)
    for cat in (ROOT / "plugins").glob("*/catalog.yaml"):
        shutil.copytree(cat.parent, tmp_path / "plugins" / cat.parent.name,
                        ignore=shutil.ignore_patterns("tests", "variants", "__pycache__"))
    return tmp_path


def test_repository_passes_with_grace_warnings(capsys) -> None:
    assert gov.main(["--today", TODAY.isoformat()]) == 0
    out = capsys.readouterr().out
    assert "second-maintainer" in out and "grace until" in out


def test_codeowners_drift(repo: Path) -> None:
    cat = repo / "plugins" / "rf-web" / "catalog.yaml"
    cat.write_text(cat.read_text().replace("maintainers:\n", "maintainers:\n  - github: new-person\n    name: New Person\n"))
    problems = gov.ownership_problems(repo)
    assert problems == ["rf-web: CODEOWNERS lists manykarim, catalog.yaml maintainers are manykarim, new-person"]


def test_codeowners_line_for_a_missing_plugin(repo: Path) -> None:
    owners = repo / ".github" / "CODEOWNERS"
    owners.write_text(owners.read_text() + "/plugins/rf-gone/ @manykarim\n")
    assert gov.ownership_problems(repo) == ["CODEOWNERS names /plugins/rf-gone/, but there is no plugin rf-gone"]


def test_verified_without_evals_is_refused(repo: Path) -> None:
    shutil.rmtree(repo / "plugins" / "rf-mobile" / "evals" / "triggers")
    fails, _ = gov.tier_problems(repo, TODAY, None)
    assert fails == ["rf-mobile (verified): trigger-sets: no trigger set for rf-appium"]


def test_grace_ends(repo: Path) -> None:
    fails, warns = gov.tier_problems(repo, dt.date(2027, 2, 1), None)
    assert warns == [] and len(fails) == 6 and all("grace ended" in f for f in fails)


def test_foundation_membership_when_known(repo: Path, tmp_path: Path) -> None:
    team = tmp_path / "team.json"
    team.write_text(json.dumps({"foundation": ["someone-else"]}))
    fails, warns = gov.tier_problems(repo, TODAY, {"someone-else"})
    assert not fails and any("foundation-maintainer" in w for w in warns)


def test_catalogs_as_yaml_text() -> None:
    snap = _snap("tier-promotion-maintainers-only")
    snap["base_catalogs"] = {"rf-db": "tier: community\nmaintainers:\n  - github: maint-c\n"}
    snap["head_catalogs"] = {"rf-db": "tier: verified\nmaintainers:\n  - github: maint-c\n"}
    assert {g.name for g in rr.required_groups(snap, rr.governance(ROOT))} == {"owners:rf-db", "foundation"}
