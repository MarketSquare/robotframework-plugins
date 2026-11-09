"""Programme manifests and the generated catalogue (spec plugin-catalogue)."""
from __future__ import annotations

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
    (d / ".claude-plugin" / "plugin.json").write_text(f'{{"name": "{name}", "version": "1.0.0"}}\n')
    if manifest is not None:
        shutil.copy(manifest, d / "catalog.yaml")
    if content:
        (d / "skills" / name).mkdir(parents=True)
        (d / "skills" / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n---\n")
    return d


def test_repository_manifests_are_valid() -> None:
    plugins = bc.load_plugins(REPO)
    assert {p.name for p in plugins} >= {"rf-agentskills"}


def test_rf_agentskills_manifest() -> None:
    """rf-agentskills is the bundle of the five plugins; the libraries moved to them."""
    by_name = {p.name: p for p in bc.load_plugins(REPO)}
    plugin = by_name["rf-agentskills"]
    assert plugin.tier == "verified" and plugin.status == "active"
    assert plugin.is_bundle and plugin.version == "4.0.0"
    assert plugin.bundled == ["rf-core", "rf-web", "rf-api", "rf-mobile", "rf-desktop"]
    assert plugin.dependencies == [] and not plugin.has_content
    assert plugin.manifest["libraries"] == []
    assert {lib["package"] for p in by_name.values() for lib in p.manifest["libraries"]} >= {
        "robotframework-browser", "robotframework-seleniumlibrary", "robotframework-appiumlibrary",
        "robotframework-requests", "RESTinstance", "robotframework-PlatynUI"}


def test_every_skill_has_one_home() -> None:
    """plugin-split: the nine skills appear once each, in the plugins the table names."""
    homes = {md.parent.name: md.parent.parent.parent.name for md in REPO.glob("plugins/*/skills/*/SKILL.md")}
    assert homes == {
        "rf-language": "rf-core", "rf-setup": "rf-core", "rf-python-library": "rf-core",
        "rf-browser": "rf-web", "rf-selenium": "rf-web", "rf-requests": "rf-api", "rf-restinstance": "rf-api",
        "rf-appium": "rf-mobile", "rf-platynui": "rf-desktop"}
    assert {f.stem for f in REPO.glob("plugins/*/agents/*.md")} == {
        "rf-test-architect", "rf-debug-expert", "rf-migration-guide"}
    assert {f.parent.parent.name for f in REPO.glob("plugins/*/agents/*.md")} == {"rf-core"}
    assert [f.parent.parent.name for f in REPO.glob("plugins/*/hooks/hooks.json")] == ["rf-core"]


def test_technology_plugins_depend_on_core() -> None:
    by_name = {p.name: p for p in bc.load_plugins(REPO)}
    for name in ("rf-web", "rf-api", "rf-mobile", "rf-desktop"):
        assert by_name[name].plugin_json["dependencies"] == [{"name": "rf-core", "version": "^1.0"}], name
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
    text = (FIXTURES / "deprecated-without-replacement.yaml").read_text().replace(
        'deprecated_since: "2026-11-08"', "deprecated_since: 2026-11-08\nreplacement: rf-example")
    src = tmp_path / "dep.yaml"
    src.write_text(text)
    _add_plugin(scratch, "rf-old", src)
    assert "rf-old" in {p.name for p in bc.load_plugins(scratch)}


# --- generated files (task 3.2) -------------------------------------------

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
    shutil.copytree(REPO / bc.BUNDLES_REL, root / bc.BUNDLES_REL)
    (root / bc.MARKETPLACE_REL).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO / bc.MARKETPLACE_REL, root / bc.MARKETPLACE_REL)
    (root / "docs").mkdir()
    shutil.copy(REPO / bc.CATALOG_DOC_REL, root / bc.CATALOG_DOC_REL)
    shutil.copy(REPO / "README.md", root / "README.md")
    (root / "installer").mkdir()
    shutil.copy(REPO / bc.INSTALLER_PYPROJECT_REL, root / bc.INSTALLER_PYPROJECT_REL)
    return root


def test_check_passes_on_the_repository() -> None:
    assert bc.main(["--check"]) == 0


def test_stale_catalogue_fails_check(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _full_scratch(tmp_path)
    manifest = root / "plugins" / "rf-core" / "catalog.yaml"
    manifest.write_text(manifest.read_text().replace("summary: Robot Framework", "summary: Changed Robot Framework"))
    assert bc.main(["--check", "--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert "README.md is out of date" in err and "python scripts/build-catalog.py" in err
    assert bc.main(["--root", str(root)]) == 0
    assert bc.main(["--check", "--root", str(root)]) == 0
    assert "Changed Robot Framework" in (root / "README.md").read_text()


def test_marketplace_tags_show_the_tier(tmp_path: Path) -> None:
    root = _full_scratch(tmp_path)
    _add_plugin(root, "rf-example", FIXTURES / "valid-community.yaml")
    assert bc.main(["--root", str(root)]) == 0
    entries = {e["name"]: e for e in json.loads((root / bc.MARKETPLACE_REL).read_text())["plugins"]}
    assert "verified" in entries["rf-agentskills"]["tags"]
    assert "community" in entries["rf-example"]["tags"]
    assert entries["rf-example"]["source"] == "./plugins/rf-example"


def test_deprecated_plugin_is_tagged_and_removed_plugin_leaves(tmp_path: Path) -> None:
    root = _full_scratch(tmp_path)
    d = _add_plugin(root, "rf-example", FIXTURES / "valid-community.yaml")
    text = (d / "catalog.yaml").read_text().replace(
        "status: active", 'status: deprecated\ndeprecated_since: "2026-11-08"\nreplacement: rf-agentskills')
    (d / "catalog.yaml").write_text(text)
    assert bc.main(["--root", str(root)]) == 0
    entries = {e["name"]: e for e in json.loads((root / bc.MARKETPLACE_REL).read_text())["plugins"]}
    assert "deprecated" in entries["rf-example"]["tags"]
    assert "deprecated, use rf-agentskills" in (root / "README.md").read_text()
    (d / "catalog.yaml").write_text(text.replace("status: deprecated", "status: removed"))
    assert bc.main(["--check", "--root", str(root)]) == 1
    assert bc.main(["--root", str(root)]) == 0
    market = json.loads((root / bc.MARKETPLACE_REL).read_text())
    assert "rf-example" not in [e["name"] for e in market["plugins"]]
    assert market["renames"] == {"rf-example": None}
    assert market["forceRemoveDeletedPlugins"] is True


# --- content, bundles and per-agent marketplaces (split-rf-agentskills) -------

def test_empty_plugin_refused(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _full_scratch(tmp_path)
    d = _add_plugin(root, "rf-database", FIXTURES / "valid-community.yaml", content=False)
    (d / "catalog.yaml").write_text((d / "catalog.yaml").read_text().replace("name: rf-example", "name: rf-database"))
    assert bc.main(["--check", "--root", str(root)]) == 1
    assert "plugins/rf-database: ships no skill, subagent or hook; a plugin needs content" in capsys.readouterr().err


def test_bundle_must_name_listed_plugins_and_ship_nothing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _full_scratch(tmp_path)
    manifest = root / "plugins" / "rf-agentskills" / "catalog.yaml"
    manifest.write_text(manifest.read_text().replace("  - rf-desktop\n", "  - rf-desktop\n  - rf-nope\n"))
    pj = root / "plugins" / "rf-agentskills" / ".claude-plugin" / "plugin.json"
    pj.write_text(json.dumps({**json.loads(pj.read_text()), "dependencies": ["rf-core"]}))
    _skill(root / "plugins" / "rf-agentskills", "rf-own")
    assert bc.main(["--check", "--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert "bundle: 'rf-nope' is not a listed plugin with content" in err
    assert "a bundle declares no dependencies" in err
    assert "a bundle ships no content of its own" in err


def test_one_marketplace_points_the_bundle_at_its_copy() -> None:
    entries = {e["name"]: e for e in json.loads((REPO / bc.MARKETPLACE_REL).read_text())["plugins"]}
    assert entries["rf-agentskills"]["source"] == "./bundles/rf-agentskills"
    assert all(e["source"] == f"./plugins/{n}" for n, e in entries.items() if n != "rf-agentskills")
    assert not (REPO / ".github" / "plugin").exists() and not (REPO / ".agents").exists()


def test_bundle_copies_match_the_plugins() -> None:
    copies = REPO / bc.BUNDLES_REL / "rf-agentskills"
    assert not list(copies.rglob("*")) or not [p for p in copies.rglob("*") if p.is_symlink()]
    assert sorted(d.name for d in (copies / "skills").iterdir()) == sorted(
        md.parent.name for md in REPO.glob("plugins/*/skills/*/SKILL.md"))
    assert (copies / "hooks" / "hooks.json").read_bytes() == (REPO / "plugins/rf-core/hooks/hooks.json").read_bytes()
    for rel in bc.BUNDLE_OWN:
        assert (copies / rel).read_bytes() == (REPO / "plugins/rf-agentskills" / rel).read_bytes(), rel
    pj = json.loads((copies / ".claude-plugin" / "plugin.json").read_text())
    assert pj["name"] == "rf-agentskills" and pj["version"] == "4.0.0" and "dependencies" not in pj


def test_stale_and_stray_bundle_copies_fail_check(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _full_scratch(tmp_path)
    md = root / "plugins" / "rf-web" / "skills" / "rf-browser" / "SKILL.md"
    md.write_text(md.read_text() + "\nEdited.\n")
    stray = root / bc.BUNDLES_REL / "rf-agentskills" / "skills" / "rf-retired" / "SKILL.md"
    stray.parent.mkdir(parents=True)
    stray.write_text("old")
    assert bc.main(["--check", "--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert "bundles/rf-agentskills/skills/rf-browser/SKILL.md is out of date" in err
    assert "bundles/rf-agentskills/skills/rf-retired/SKILL.md is not generated any more" in err
    assert bc.main(["--root", str(root)]) == 0
    assert not stray.exists()
    assert bc.main(["--check", "--root", str(root)]) == 0


# --- cross-plugin checks (task 3.8) ----------------------------------------

def _skill(plugin_dir: Path, name: str) -> None:
    d = plugin_dir / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n---\n")


def test_marketplace_sets_force_remove() -> None:
    assert json.loads((REPO / bc.MARKETPLACE_REL).read_text())["forceRemoveDeletedPlugins"] is True


def test_duplicate_skill_name(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _full_scratch(tmp_path)
    _skill(_add_plugin(root, "rf-web-extra", FIXTURES / "valid-community.yaml"), "rf-browser")
    (root / "plugins" / "rf-web-extra" / "catalog.yaml").write_text(
        (root / "plugins" / "rf-web-extra" / "catalog.yaml").read_text().replace("name: rf-example", "name: rf-web-extra"))
    assert bc.main(["--check", "--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert "skill 'rf-browser' is shipped by more than one plugin: rf-web, rf-web-extra" in err


def test_duplicate_subagent_and_hook_install_path(tmp_path: Path) -> None:
    root = _full_scratch(tmp_path)
    for name in ("rf-web", "rf-example"):
        d = root / "plugins" / name if name == "rf-web" else _add_plugin(root, name, FIXTURES / "valid-community.yaml")
        (d / "agents").mkdir()
        (d / "agents" / f"{name}-agent.md").write_text("---\nname: rf-reviewer\n---\n")
        (d / "variants" / "opencode" / "plugins").mkdir(parents=True)
        (d / "variants" / "opencode" / "plugins" / "rf-hooks.js").write_text("")
    problems = bc.name_problems(bc.load_plugins(root))
    assert problems == [
        "hook install path 'plugins/rf-hooks.js' is shipped by more than one plugin: rf-example, rf-web",
        "subagent 'rf-reviewer' is shipped by more than one plugin: rf-example, rf-web",
    ]


def test_deprecated_plugin_names_count_removed_do_not(tmp_path: Path) -> None:
    root = _full_scratch(tmp_path)
    d = _add_plugin(root, "rf-example", FIXTURES / "valid-community.yaml")
    _skill(d, "rf-browser")
    text = (d / "catalog.yaml").read_text().replace(
        "status: active", 'status: deprecated\ndeprecated_since: "2026-11-08"\nreplacement: rf-agentskills')
    (d / "catalog.yaml").write_text(text)
    assert bc.name_problems(bc.load_plugins(root))
    (d / "catalog.yaml").write_text(text.replace("status: deprecated", "status: removed"))
    assert bc.name_problems(bc.load_plugins(root)) == []


def test_link_outside_the_repository(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _full_scratch(tmp_path)
    outside = tmp_path / "outside.mjs"
    outside.write_text("")
    scripts = root / "plugins" / "rf-core" / "scripts"
    (scripts / "escape.mjs").symlink_to(Path("../../../../outside.mjs"))
    (scripts / "absolute.mjs").symlink_to(outside)
    assert bc.main(["--check", "--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert "plugins/rf-core/scripts/escape.mjs: symlink points outside the repository" in err
    assert "plugins/rf-core/scripts/absolute.mjs: symlink target" in err


def test_link_inside_the_repository_passes(tmp_path: Path) -> None:
    root = _full_scratch(tmp_path)
    owner = root / "plugins" / "rf-core" / "scripts"
    (owner / "shared.mjs").write_text("")
    d = _add_plugin(root, "rf-example", FIXTURES / "valid-community.yaml")
    (d / "scripts").mkdir()
    (d / "scripts" / "shared.mjs").symlink_to(Path("../../rf-core/scripts/shared.mjs"))
    assert bc.symlink_problems(root, bc.load_plugins(root)) == []


@pytest.mark.parametrize(
    ("current", "message"),
    [
        ({"rf-new": None}, "entry 'rf-old' (-> None) was deleted"),
        ({"rf-old": "rf-agentskills", "rf-new": None}, "entry 'rf-old' changed from None to 'rf-agentskills'"),
    ],
)
def test_renames_history_is_append_only(current: dict, message: str) -> None:
    (problem,) = bc.renames_problems({"rf-old": None}, current)
    assert message in problem
    assert bc.renames_problems({"rf-old": None}, {"rf-old": None, "rf-new": "rf-agentskills"}) == []


def test_renames_check_reads_the_base_ref(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import subprocess
    root = _full_scratch(tmp_path)
    market = root / bc.MARKETPLACE_REL
    data = json.loads(market.read_text())
    data["renames"] = {"rf-old": None}
    market.write_text(bc._dump_json(data))
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-C", str(root)]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "base"], check=True)
    assert bc.main(["--check", "--root", str(root), "--base", "HEAD"]) == 0
    del data["renames"]
    market.write_text(bc._dump_json(data))
    assert bc.main(["--root", str(root)]) == 0
    assert bc.main(["--check", "--root", str(root), "--base", "HEAD"]) == 1
    assert "entry 'rf-old' (-> None) was deleted" in capsys.readouterr().err


# --- version table (task 3.9) ----------------------------------------------

def test_version_table_is_headed_by_the_installer_version(capsys: pytest.CaptureFixture[str]) -> None:
    version = bc.installer_version(REPO)
    plugin = json.loads((REPO / "plugins/rf-agentskills/.claude-plugin/plugin.json").read_text())["version"]
    assert bc.main(["--version-table"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == f"| robotframework-plugins {version} bundles | Version | Tier |"
    assert f"| `rf-agentskills` | {plugin} | verified |" in lines
    for doc in ("README.md", "docs/catalog.md"):
        assert lines[0] in (REPO / doc).read_text()


def test_version_bump_without_regeneration_fails_check(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _full_scratch(tmp_path)
    pj = root / "plugins/rf-agentskills/.claude-plugin/plugin.json"
    data = json.loads(pj.read_text())
    data["version"] = "99.0.0"
    pj.write_text(json.dumps(data))
    assert bc.main(["--check", "--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert "README.md is out of date" in err and "docs/catalog.md is out of date" in err
    assert bc.main(["--root", str(root)]) == 0
    assert "| `rf-agentskills` | 99.0.0 | verified |" in (root / "docs/catalog.md").read_text()


def test_installer_version_bump_without_regeneration_fails_check(tmp_path: Path) -> None:
    root = _full_scratch(tmp_path)
    pyproject = root / bc.INSTALLER_PYPROJECT_REL
    old = bc.installer_version(root)
    pyproject.write_text(pyproject.read_text().replace(f'version = "{old}"', 'version = "2099.1.0"', 1))
    assert bc.main(["--check", "--root", str(root)]) == 1
    assert bc.main(["--root", str(root)]) == 0
    assert "robotframework-plugins 2099.1.0 bundles" in (root / "README.md").read_text()
