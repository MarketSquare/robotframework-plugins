"""Programme manifests and the generated catalogue (spec plugin-catalogue)."""
from __future__ import annotations

import datetime as _dt
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures" / "catalog"

_spec = importlib.util.spec_from_file_location("build_catalog", REPO / "scripts" / "build-catalog.py")
bc = importlib.util.module_from_spec(_spec)
sys.modules["build_catalog"] = bc
_spec.loader.exec_module(bc)


@pytest.fixture
def scratch(tmp_path: Path) -> Path:
    """A minimal repository copy: schema plus the real plugin manifests."""
    (tmp_path / "schemas").mkdir()
    shutil.copy(REPO / bc.SCHEMA_REL, tmp_path / bc.SCHEMA_REL)
    for d in (REPO / "plugins").iterdir():
        if d.is_dir():
            dst = tmp_path / "plugins" / d.name
            (dst / ".claude-plugin").mkdir(parents=True)
            shutil.copy(d / "catalog.yaml", dst / "catalog.yaml")
            shutil.copy(d / ".claude-plugin" / "plugin.json", dst / ".claude-plugin" / "plugin.json")
    return tmp_path


def _add_plugin(root: Path, name: str, manifest: Path | None, *, content: bool = True) -> Path:
    """A plugin dir; with ``content``, one skill named after it (a listed plugin needs content)."""
    d = root / "plugins" / name
    (d / ".claude-plugin").mkdir(parents=True)
    (d / ".claude-plugin" / "plugin.json").write_text(f'{{"name": "{name}", "version": "1.0.0"}}\n', encoding="utf-8")
    if manifest is not None:
        shutil.copy(manifest, d / "catalog.yaml")
    if content:
        (d / "skills" / name).mkdir(parents=True)
        (d / "skills" / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n---\n", encoding="utf-8")
    return d


def test_repository_manifests_are_valid() -> None:
    plugins = bc.load_plugins(REPO)
    # >=: the template check adds plugins/example to a scratch copy.
    assert {p.name for p in plugins} >= {"rf-core", "rf-api", "rf-desktop", "rf-mobile", "rf-web"}
    assert "rf-agentskills" not in {p.name for p in plugins}


def test_libraries_live_in_the_plugins() -> None:
    by_name = {p.name: p for p in bc.load_plugins(REPO)}
    assert "rf-agentskills" not in by_name
    assert {lib["package"] for p in by_name.values() for lib in p.manifest["libraries"]} >= {
        "robotframework-browser", "robotframework-seleniumlibrary", "robotframework-appiumlibrary",
        "robotframework-requests", "RESTinstance", "robotframework-PlatynUI"}

def test_every_skill_has_one_home() -> None:
    """plugin-split: the nine skills appear once each, in the plugins the table names."""
    homes = {md.parent.name: md.parent.parent.parent.name for md in REPO.glob("plugins/*/skills/*/SKILL.md")}
    split = {
        "rf-language": "rf-core", "rf-setup": "rf-core", "rf-python-library": "rf-core",
        "rf-browser": "rf-web", "rf-selenium": "rf-web", "rf-requests": "rf-api", "rf-restinstance": "rf-api",
        "rf-appium": "rf-mobile", "rf-platynui": "rf-desktop"}
    # Other plugins (a community plugin, the template in CI) may add skills.
    assert {k: homes.get(k) for k in split} == split
    assert {f.stem for f in REPO.glob("plugins/*/agents/*.md")} == {
        "rf-test-architect", "rf-debug-expert", "rf-migration-guide"}
    assert {f.parent.parent.name for f in REPO.glob("plugins/*/agents/*.md")} == {"rf-core"}
    assert [f.parent.parent.name for f in REPO.glob("plugins/*/hooks/hooks.json")] == ["rf-core"]


def test_technology_plugins_depend_on_core() -> None:
    by_name = {p.name: p for p in bc.load_plugins(REPO)}
    for name in ("rf-web", "rf-api", "rf-mobile", "rf-desktop"):
        assert by_name[name].plugin_json["dependencies"] == ["rf-core"], name
    assert "dependencies" not in by_name["rf-core"].plugin_json


def test_valid_fixture_passes(scratch: Path) -> None:
    _add_plugin(scratch, "rf-example", FIXTURES / "valid-community.yaml")
    assert "rf-example" in {p.name for p in bc.load_plugins(scratch)}


def test_missing_manifest_fails(scratch: Path) -> None:
    _add_plugin(scratch, "new-plugin", None)
    with pytest.raises(bc.CatalogError) as exc:
        bc.load_plugins(scratch)
    assert any("plugins/new-plugin/catalog.yaml: missing" in p for p in exc.value.problems)


def test_deprecated_without_replacement_fails(scratch: Path) -> None:
    _add_plugin(scratch, "rf-old", FIXTURES / "deprecated-without-replacement.yaml")
    with pytest.raises(bc.CatalogError) as exc:
        bc.load_plugins(scratch)
    assert any("rf-old/catalog.yaml" in p and "replacement" in p for p in exc.value.problems)


def test_name_must_match_directory(scratch: Path) -> None:
    d = _add_plugin(scratch, "rf-other", FIXTURES / "valid-community.yaml")
    assert d.name != "rf-example"
    with pytest.raises(bc.CatalogError) as exc:
        bc.load_plugins(scratch)
    assert any("differs from the directory name" in p for p in exc.value.problems)


def test_unquoted_date_is_accepted(scratch: Path, tmp_path: Path) -> None:
    text = (FIXTURES / "deprecated-without-replacement.yaml").read_text(encoding="utf-8").replace(
        'deprecated_since: "2026-11-08"', "deprecated_since: 2026-11-08\nreplacement: rf-example")
    src = tmp_path / "dep.yaml"
    src.write_text(text, encoding="utf-8")
    _add_plugin(scratch, "rf-old", src)
    assert "rf-old" in {p.name for p in bc.load_plugins(scratch)}


# --- generated files (task 3.2) -------------------------------------------

def _releases(root: Path, *releases: tuple[str, str]) -> None:
    """CHANGELOG.md with these releases (newest first, as written)."""
    path = root / bc.CHANGELOG_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(f"## {v} — {d}\n\n- Changes.\n\n" for v, d in reversed(releases))
    path.write_text("# Changelog\n\n## Unreleased\n\n" + body + "## 2026.12.0rc1 — 2026-11-01 (pre-release)\n", encoding="utf-8")


def _full_scratch(tmp_path: Path) -> Path:
    """Scratch repo with the generated files too, so --check can run on it."""
    root = tmp_path / "repo"
    (root / "schemas").mkdir(parents=True)
    shutil.copy(REPO / bc.SCHEMA_REL, root / bc.SCHEMA_REL)
    def ignore(directory: str, names: list[str]) -> set[str]:
        # A plugin's own tests/, evals/ and variants/; skills keep their example tests/.
        top = Path(directory).parent == REPO / "plugins"
        return {n for n in names if n == "__pycache__" or (top and n in ("variants", "tests", "evals"))}

    shutil.copytree(REPO / "plugins", root / "plugins", ignore=ignore)
    (root / bc.MARKETPLACE_REL).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO / bc.MARKETPLACE_REL, root / bc.MARKETPLACE_REL)
    (root / "docs").mkdir()
    shutil.copy(REPO / bc.CATALOG_DOC_REL, root / bc.CATALOG_DOC_REL)
    shutil.copy(REPO / "README.md", root / "README.md")
    (root / "installer").mkdir()
    shutil.copy(REPO / bc.INSTALLER_PYPROJECT_REL, root / bc.INSTALLER_PYPROJECT_REL)
    (root / bc.INIT_REL).parent.mkdir(parents=True)
    shutil.copy(REPO / bc.INIT_REL, root / bc.INIT_REL)
    return root


def _set_release(root: Path, version: str) -> None:
    pyproject = root / bc.INSTALLER_PYPROJECT_REL
    old = bc.installer_version(root)
    pyproject.write_text(pyproject.read_text(encoding="utf-8").replace(f'version = "{old}"', f'version = "{version}"', 1),
                         encoding="utf-8")


def test_check_passes_on_the_repository() -> None:
    assert bc.main(["--check"]) == 0


def test_stale_catalogue_fails_check(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _full_scratch(tmp_path)
    manifest = root / "plugins" / "rf-core" / "catalog.yaml"
    manifest.write_text(manifest.read_text(encoding="utf-8").replace("summary: Robot Framework", "summary: Changed Robot Framework"), encoding="utf-8")
    assert bc.main(["--check", "--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert "README.md is out of date" in err and "python scripts/build-catalog.py" in err
    assert bc.main(["--root", str(root)]) == 0
    assert bc.main(["--check", "--root", str(root)]) == 0
    assert "Changed Robot Framework" in (root / "README.md").read_text(encoding="utf-8")


def test_marketplace_tags_show_the_tier(tmp_path: Path) -> None:
    root = _full_scratch(tmp_path)
    _add_plugin(root, "rf-example", FIXTURES / "valid-community.yaml")
    assert bc.main(["--root", str(root)]) == 0
    entries = {e["name"]: e for e in json.loads((root / bc.MARKETPLACE_REL).read_text(encoding="utf-8"))["plugins"]}
    assert "verified" in entries["rf-core"]["tags"]
    assert "community" in entries["rf-example"]["tags"]
    assert entries["rf-example"]["source"] == "./plugins/rf-example"


def test_deprecated_plugin_is_tagged_and_removed_plugin_leaves(tmp_path: Path) -> None:
    root = _full_scratch(tmp_path)
    d = _add_plugin(root, "rf-example", FIXTURES / "valid-community.yaml")
    text = (d / "catalog.yaml").read_text(encoding="utf-8").replace(
        "status: active", 'status: deprecated\ndeprecated_since: "2026-08-01"\nreplacement: rf-core')
    (d / "catalog.yaml").write_text(text, encoding="utf-8")
    _releases(root, ("2026.9.0", "2026-09-10"), ("2026.10.0", "2026-10-12"))
    assert bc.main(["--root", str(root)]) == 0
    entries = {e["name"]: e for e in json.loads((root / bc.MARKETPLACE_REL).read_text(encoding="utf-8"))["plugins"]}
    assert "deprecated" in entries["rf-example"]["tags"]
    assert "deprecated, use rf-core" in (root / "README.md").read_text(encoding="utf-8")
    (d / "catalog.yaml").write_text(text.replace("status: deprecated", "status: removed"), encoding="utf-8")
    assert bc.main(["--check", "--root", str(root), "--today", "2026-11-09"]) == 1
    assert bc.main(["--root", str(root), "--today", "2026-11-09"]) == 0
    market = json.loads((root / bc.MARKETPLACE_REL).read_text(encoding="utf-8"))
    assert "rf-example" not in [e["name"] for e in market["plugins"]]
    assert market["renames"] == {"rf-agentskills": None, "rf-example": None}
    assert market["forceRemoveDeletedPlugins"] is True


# --- content and the one marketplace (split-rf-agentskills, single-release-version) --

def test_empty_plugin_refused(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _full_scratch(tmp_path)
    d = _add_plugin(root, "rf-database", FIXTURES / "valid-community.yaml", content=False)
    (d / "catalog.yaml").write_text((d / "catalog.yaml").read_text(encoding="utf-8").replace("name: rf-example", "name: rf-database"), encoding="utf-8")
    assert bc.main(["--check", "--root", str(root)]) == 1
    assert "plugins/rf-database: ships no skill, subagent or hook; a plugin needs content" in capsys.readouterr().err


def test_bundle_key_refused(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The rf-agentskills bundle was removed in 5.0.0; catalog.yaml has no bundle field."""
    root = _full_scratch(tmp_path)
    manifest = root / "plugins" / "rf-web" / "catalog.yaml"
    manifest.write_text(manifest.read_text(encoding="utf-8") + "bundle:\n  - rf-core\n", encoding="utf-8")
    assert bc.main(["--check", "--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert "plugins/rf-web/catalog.yaml" in err and "'bundle'" in err


def test_dependency_version_range_refused(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _full_scratch(tmp_path)
    pj = root / "plugins" / "rf-web" / ".claude-plugin" / "plugin.json"
    data = json.loads(pj.read_text(encoding="utf-8"))
    data["dependencies"] = [{"name": "rf-core", "version": "^1.0"}]
    pj.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    assert bc.main(["--check", "--root", str(root)]) == 1
    assert "plugins/rf-web/.claude-plugin/plugin.json: dependency 'rf-core' has a version range ('^1.0')" in (
        capsys.readouterr().err)


def test_one_marketplace_lists_the_plugins_rf_core_first() -> None:
    market = json.loads((REPO / bc.MARKETPLACE_REL).read_text(encoding="utf-8"))
    names = [e["name"] for e in market["plugins"]]
    assert names[0] == "rf-core" and names[1:] == sorted(names[1:])
    assert set(names) >= {"rf-api", "rf-desktop", "rf-mobile", "rf-web"} and "rf-agentskills" not in names
    assert all(e["source"] == f"./plugins/{e['name']}" for e in market["plugins"])
    assert market["renames"]["rf-agentskills"] is None
    assert not (REPO / "bundles").exists() and not (REPO / "plugins" / "rf-agentskills").exists()
    assert not (REPO / ".github" / "plugin").exists() and not (REPO / ".agents").exists()

def _skill(plugin_dir: Path, name: str) -> None:
    d = plugin_dir / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n---\n", encoding="utf-8")


def test_marketplace_sets_force_remove() -> None:
    assert json.loads((REPO / bc.MARKETPLACE_REL).read_text(encoding="utf-8"))["forceRemoveDeletedPlugins"] is True


def test_duplicate_skill_name(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _full_scratch(tmp_path)
    _skill(_add_plugin(root, "rf-web-extra", FIXTURES / "valid-community.yaml"), "rf-browser")
    (root / "plugins" / "rf-web-extra" / "catalog.yaml").write_text(
        (root / "plugins" / "rf-web-extra" / "catalog.yaml").read_text(encoding="utf-8").replace("name: rf-example", "name: rf-web-extra"), encoding="utf-8")
    assert bc.main(["--check", "--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert "skill 'rf-browser' is shipped by more than one plugin: rf-web, rf-web-extra" in err


def test_duplicate_subagent_and_hook_install_path(tmp_path: Path) -> None:
    root = _full_scratch(tmp_path)
    for name in ("rf-web", "rf-example"):
        d = root / "plugins" / name if name == "rf-web" else _add_plugin(root, name, FIXTURES / "valid-community.yaml")
        (d / "agents").mkdir()
        (d / "agents" / f"{name}-agent.md").write_text("---\nname: rf-reviewer\n---\n", encoding="utf-8")
        (d / "variants" / "opencode" / "plugins").mkdir(parents=True)
        (d / "variants" / "opencode" / "plugins" / "rf-hooks.js").write_text("", encoding="utf-8")
    problems = bc.name_problems(bc.load_plugins(root))
    assert problems == [
        "hook install path 'plugins/rf-hooks.js' is shipped by more than one plugin: rf-example, rf-web",
        "subagent 'rf-reviewer' is shipped by more than one plugin: rf-example, rf-web",
    ]


def test_deprecated_plugin_names_count_removed_do_not(tmp_path: Path) -> None:
    root = _full_scratch(tmp_path)
    d = _add_plugin(root, "rf-example", FIXTURES / "valid-community.yaml")
    _skill(d, "rf-browser")
    text = (d / "catalog.yaml").read_text(encoding="utf-8").replace(
        "status: active", 'status: deprecated\ndeprecated_since: "2026-11-08"\nreplacement: rf-core')
    (d / "catalog.yaml").write_text(text, encoding="utf-8")
    assert bc.name_problems(bc.load_plugins(root))
    (d / "catalog.yaml").write_text(text.replace("status: deprecated", "status: removed"), encoding="utf-8")
    assert bc.name_problems(bc.load_plugins(root)) == []


def test_symlinks_in_a_plugin_fail(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Codex drops symlinks: plugins carry none, inside or outside the repository."""
    root = _full_scratch(tmp_path)
    outside = tmp_path / "outside.mjs"
    outside.write_text("", encoding="utf-8")
    scripts = root / "plugins" / "rf-core" / "scripts"
    (scripts / "escape.mjs").symlink_to(Path("../../../../outside.mjs"))
    (scripts / "absolute.mjs").symlink_to(outside)
    d = _add_plugin(root, "rf-example", FIXTURES / "valid-community.yaml")
    (d / "scripts").mkdir()
    (d / "scripts" / "shared.mjs").symlink_to(Path("../../rf-core/scripts/_hook_input.mjs"))
    assert bc.main(["--check", "--root", str(root)]) == 1
    err = capsys.readouterr().err
    for rel in ("plugins/rf-core/scripts/escape.mjs", "plugins/rf-core/scripts/absolute.mjs",
                "plugins/rf-example/scripts/shared.mjs"):
        assert f"{rel}: plugins can't contain symlinks" in err, rel


@pytest.mark.parametrize(
    ("current", "message"),
    [
        ({"rf-new": None}, "entry 'rf-old' (-> None) was deleted"),
        ({"rf-old": "rf-core", "rf-new": None}, "entry 'rf-old' changed from None to 'rf-core'"),
    ],
)
def test_renames_history_is_append_only(current: dict, message: str) -> None:
    (problem,) = bc.renames_problems({"rf-old": None}, current)
    assert message in problem
    assert bc.renames_problems({"rf-old": None}, {"rf-old": None, "rf-new": "rf-core"}) == []


def test_renames_check_reads_the_base_ref(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import subprocess
    root = _full_scratch(tmp_path)
    market = root / bc.MARKETPLACE_REL
    data = json.loads(market.read_text(encoding="utf-8"))
    data["renames"] = {"rf-old": None}
    market.write_text(bc._dump_json(data), encoding="utf-8")
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-C", str(root)]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "base"], check=True)
    assert bc.main(["--check", "--root", str(root), "--base", "HEAD"]) == 0
    del data["renames"]
    market.write_text(bc._dump_json(data), encoding="utf-8")
    assert bc.main(["--root", str(root)]) == 0
    assert bc.main(["--check", "--root", str(root), "--base", "HEAD"]) == 1
    assert "entry 'rf-old' (-> None) was deleted" in capsys.readouterr().err


# --- one release version (release-train) ------------------------------------

def test_every_copy_carries_the_release_version() -> None:
    version = bc.installer_version(REPO)
    for p in bc.listed(bc.load_plugins(REPO)):
        assert p.version == bc.plugin_version(version), p.name
    assert f'__version__ = "{version}"' in (REPO / bc.INIT_REL).read_text(encoding="utf-8")
    assert f"Release **{version}**" in (REPO / "README.md").read_text(encoding="utf-8")
    assert f"Release **{version}**" in (REPO / bc.CATALOG_DOC_REL).read_text(encoding="utf-8")


def test_version_table_names_the_release(capsys: pytest.CaptureFixture[str]) -> None:
    version = bc.installer_version(REPO)
    assert bc.main(["--version-table"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == f"| robotframework-plugins {version} includes | Tier |"
    assert "| `rf-core` | verified |" in lines


def test_plugin_version_out_of_step_fails_check(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _full_scratch(tmp_path)
    version = bc.installer_version(root)
    pj = root / "plugins/rf-web/.claude-plugin/plugin.json"
    data = json.loads(pj.read_text(encoding="utf-8"))
    data["version"] = "99.0.0"
    pj.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    assert bc.main(["--check", "--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert (f"plugins/rf-web/.claude-plugin/plugin.json: version '99.0.0' differs from the release version "
            f"'{version}'") in err
    assert bc.main(["--root", str(root)]) == 0
    assert json.loads(pj.read_text(encoding="utf-8"))["version"] == version
    assert bc.main(["--check", "--root", str(root)]) == 0


def test_release_bump_regenerates_every_copy(tmp_path: Path) -> None:
    root = _full_scratch(tmp_path)
    _set_release(root, "5.1.0")
    assert bc.main(["--check", "--root", str(root)]) == 1
    assert bc.main(["--root", str(root)]) == 0
    assert '__version__ = "5.1.0"' in (root / bc.INIT_REL).read_text(encoding="utf-8")
    assert "Release **5.1.0**" in (root / "README.md").read_text(encoding="utf-8")
    for pj in (root / "plugins").glob("*/.claude-plugin/plugin.json"):
        data = json.loads(pj.read_text(encoding="utf-8"))
        assert data["version"] == "5.1.0" and list(data)[:2] == ["name", "version"], pj


def test_candidate_is_semver_in_plugins(tmp_path: Path) -> None:
    root = _full_scratch(tmp_path)
    _set_release(root, "5.1.0rc1")
    assert bc.main(["--root", str(root)]) == 0
    assert bc.main(["--check", "--root", str(root)]) == 0
    assert '__version__ = "5.1.0rc1"' in (root / bc.INIT_REL).read_text(encoding="utf-8")
    for pj in (root / "plugins").glob("*/.claude-plugin/plugin.json"):
        assert json.loads(pj.read_text(encoding="utf-8"))["version"] == "5.1.0-rc.1", pj


@pytest.mark.parametrize("version", ["3.0.0", "2.9.9", "1.1.0", "5.0", "2026.11.0.dev1"])
def test_version_at_or_below_the_old_tags_refused(tmp_path: Path, version: str,
                                                  capsys: pytest.CaptureFixture[str]) -> None:
    root = _full_scratch(tmp_path)
    _set_release(root, version)
    assert bc.main(["--root", str(root)]) == 1
    assert f"installer/pyproject.toml: version '{version}'" in capsys.readouterr().err


# --- lifecycle (plugin-lifecycle; launch task 7.1) --------------------------

def _removed(root: Path, since: str) -> Path:
    d = _add_plugin(root, "rf-example", FIXTURES / "valid-community.yaml")
    (d / "catalog.yaml").write_text((d / "catalog.yaml").read_text(encoding="utf-8").replace(
        "status: active", f'status: removed\ndeprecated_since: "{since}"\nreplacement: rf-core'), encoding="utf-8")
    return d


def test_removal_too_early(scratch: Path) -> None:
    _removed(scratch, "2026-10-01")
    _releases(scratch, ("2026.10.0", "2026-10-20"))
    (problem,) = bc.lifecycle_problems(scratch, bc.load_plugins(scratch), {"plugins": []}, _dt.date(2026, 11, 9))
    assert "removed too early: deprecated since 2026-10-01, with 1 installer release(s) since (2026.10.0)" in problem
    assert "Earliest: after 1 more installer release, and not before 2026-12-30" in problem


def test_removal_after_two_releases_and_ninety_days(scratch: Path) -> None:
    _removed(scratch, "2026-08-01")
    _releases(scratch, ("2026.7.0", "2026-07-15"), ("2026.9.0", "2026-09-10"), ("2026.10.0", "2026-10-12"))
    plugins = bc.load_plugins(scratch)
    assert bc.lifecycle_problems(scratch, plugins, {"plugins": []}, _dt.date(2026, 11, 9)) == []
    # Two releases but not yet 90 days; pre-releases don't count.
    assert bc.lifecycle_problems(scratch, plugins, {"plugins": []}, _dt.date(2026, 10, 15))
    assert bc.installer_releases(scratch)[-1] == ("2026.10.0", _dt.date(2026, 10, 12))


def test_marketplace_must_not_list_a_removed_plugin(scratch: Path) -> None:
    _removed(scratch, "2026-01-01")
    _releases(scratch, ("2026.2.0", "2026-02-10"), ("2026.3.0", "2026-03-10"))
    problems = bc.lifecycle_problems(scratch, bc.load_plugins(scratch), {"plugins": [{"name": "rf-example"}]},
                                     _dt.date(2026, 11, 9))
    assert problems == [".claude-plugin/marketplace.json: lists rf-example, which is removed"]


def test_last_maintainer_leaves(scratch: Path) -> None:
    d = _add_plugin(scratch, "rf-example", FIXTURES / "valid-community.yaml")
    text = (d / "catalog.yaml").read_text(encoding="utf-8").replace("maintainers:\n  - github: someone\n", "maintainers: []\n")
    (d / "catalog.yaml").write_text(text, encoding="utf-8")
    (problem,) = bc.lifecycle_problems(scratch, bc.load_plugins(scratch), {"plugins": []}, _dt.date(2026, 11, 9))
    assert "no maintainers left; set status: deprecated" in problem
    (d / "catalog.yaml").write_text(text.replace(
        "status: active", 'status: deprecated\ndeprecated_since: "2026-11-09"\nreplacement: rf-core'), encoding="utf-8")
    assert bc.lifecycle_problems(scratch, bc.load_plugins(scratch), {"plugins": []}, _dt.date(2026, 11, 9)) == []


def test_feedback_form_lists_the_listed_plugins(tmp_path: Path) -> None:
    """adoption-reporting: the feedback form's dropdown is generated from the catalogue."""
    root = _full_scratch(tmp_path)
    form = root / bc.FEEDBACK_FORM_REL
    form.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO / bc.FEEDBACK_FORM_REL, form)
    _add_plugin(root, "rf-example", FIXTURES / "valid-community.yaml")
    assert bc.main(["--check", "--root", str(root)]) == 1
    assert bc.main(["--root", str(root)]) == 0
    assert "        - rf-example\n" in form.read_text(encoding="utf-8")


# --- libraries[].skills (catalog-library-skills; issue #7) -------------------------------


def _library_variant(tmp_path: Path, extra: str) -> Path:
    """The community fixture with ``extra`` lines added to its one library entry."""
    text = (FIXTURES / "valid-community.yaml").read_text(encoding="utf-8").replace(
        '    versions: ">=2"\n', '    versions: ">=2"\n' + extra)
    path = tmp_path / "variant.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_skills_per_library_accepted(scratch: Path, tmp_path: Path) -> None:
    _add_plugin(scratch, "rf-example", _library_variant(tmp_path, "    skills: [rf-example]\n"))
    plugins = bc.load_plugins(scratch)
    example = next(p for p in plugins if p.name == "rf-example")
    assert example.manifest["libraries"][0]["skills"] == ["rf-example"]
    assert bc.library_skill_problems([example]) == []


@pytest.mark.parametrize(("extra", "field"), [
    ("    skill: rf-example\n", "skill"),        # other unknown keys stay rejected
    ("    skills: []\n", "skills"),             # minItems 1
    ("    skills: [rf-example, rf-example]\n", "skills"),  # unique
    ("    skills: [RF_Example]\n", "skills"),   # kebab-case
])
def test_invalid_skills_field_rejected(scratch: Path, tmp_path: Path, extra: str, field: str) -> None:
    _add_plugin(scratch, "rf-example", _library_variant(tmp_path, extra))
    with pytest.raises(bc.CatalogError) as exc:
        bc.load_plugins(scratch)
    assert any("rf-example/catalog.yaml" in p and ("libraries/0" in p) and field in p for p in exc.value.problems), \
        exc.value.problems


def test_missing_skill_reported(scratch: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _add_plugin(scratch, "rf-example", _library_variant(tmp_path, "    skills: [rf-example, rf-example-auth]\n"))
    example = next(p for p in bc.load_plugins(scratch) if p.name == "rf-example")
    assert bc.library_skill_problems([example]) == [
        "rf-example: library DatabaseLibrary lists skill rf-example-auth, but "
        "plugins/rf-example/skills/rf-example-auth/SKILL.md doesn't exist"]


def test_missing_skill_fails_the_check(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "repo"
    shutil.copytree(REPO, root, ignore=shutil.ignore_patterns(".git", ".venv", "node_modules", "__pycache__",
                                                             "_assets", "eval", "openspec", "docs"))
    (root / "docs").mkdir()
    shutil.copy(REPO / "docs" / "catalog.md", root / "docs" / "catalog.md")
    manifest = root / "plugins" / "rf-api" / "catalog.yaml"
    manifest.write_text(manifest.read_text(encoding="utf-8").replace(
        "skills: [rf-requests]", "skills: [rf-requests-auth]"), encoding="utf-8")
    assert bc.main(["--check", "--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert "rf-api: library RequestsLibrary lists skill rf-requests-auth" in err


def test_removed_plugin_with_a_stale_skill_is_reported(scratch: Path, tmp_path: Path) -> None:
    text = _library_variant(tmp_path, "    skills: [rf-gone]\n").read_text(encoding="utf-8").replace(
        "status: active", 'status: removed\nreplacement: rf-core\ndeprecated_since: "2026-01-01"')
    path = tmp_path / "removed.yaml"
    path.write_text(text, encoding="utf-8")
    _add_plugin(scratch, "rf-example", path, content=False)
    example = next(p for p in bc.load_plugins(scratch) if p.name == "rf-example")
    assert len(bc.library_skill_problems([example])) == 1


def test_catalog_doc_names_the_skills_of_each_library() -> None:
    text = (REPO / "docs" / "catalog.md").read_text(encoding="utf-8")
    assert "  - Browser (`robotframework-browser` `>=20,<21`): `rf-browser`" in text
    assert "  - SeleniumLibrary (`robotframework-seleniumlibrary` `>=6.9,<7`): `rf-selenium`" in text
    assert bc._library_line({"name": "X", "package": "x", "versions": ">=1"}) == "X (`x` `>=1`)"


def test_stale_catalog_doc_fails_after_a_skills_change(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "repo"
    shutil.copytree(REPO, root, ignore=shutil.ignore_patterns(".git", ".venv", "node_modules", "__pycache__",
                                                             "_assets", "eval", "openspec"))
    manifest = root / "plugins" / "rf-web" / "catalog.yaml"
    manifest.write_text(manifest.read_text(encoding="utf-8").replace(
        "skills: [rf-selenium]", "skills: [rf-selenium, rf-browser]"), encoding="utf-8")
    assert bc.main(["--check", "--root", str(root)]) == 1
    assert "docs/catalog.md is out of date" in capsys.readouterr().err


def test_every_technology_library_names_its_skills() -> None:
    """Each library of an active technology plugin names its skills, and
    together they cover every skill the plugin ships."""
    for p in bc.load_plugins(REPO):
        if p.status != "active" or not p.manifest["libraries"]:
            continue
        named = set()
        for lib in p.manifest["libraries"]:
            assert lib.get("skills"), f"{p.name}: {lib['name']} names no skills"
            named |= set(lib["skills"])
        shipped = {d.name for d in (p.path / "skills").glob("*") if (d / "SKILL.md").is_file()}
        assert named == shipped, p.name
    assert bc.library_skill_problems(bc.load_plugins(REPO)) == []
