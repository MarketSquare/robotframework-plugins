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


def _add_plugin(root: Path, name: str, manifest: Path | None) -> Path:
    d = root / "plugins" / name
    (d / ".claude-plugin").mkdir(parents=True)
    (d / ".claude-plugin" / "plugin.json").write_text(f'{{"name": "{name}", "version": "1.0.0"}}\n')
    if manifest is not None:
        shutil.copy(manifest, d / "catalog.yaml")
    return d


def test_repository_manifests_are_valid() -> None:
    plugins = bc.load_plugins(REPO)
    assert {p.name for p in plugins} >= {"rf-agentskills"}


def test_rf_agentskills_manifest() -> None:
    (plugin,) = [p for p in bc.load_plugins(REPO) if p.name == "rf-agentskills"]
    assert plugin.tier == "verified" and plugin.status == "active"
    assert {lib["package"] for lib in plugin.manifest["libraries"]} >= {
        "robotframework-browser", "robotframework-seleniumlibrary", "robotframework-appiumlibrary",
        "robotframework-requests", "RESTinstance", "robotframework-PlatynUI"}


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
    shutil.copytree(REPO / "plugins", root / "plugins",
                    ignore=shutil.ignore_patterns("skills", "agents", "hooks", "scripts", "variants", "__pycache__"))
    (root / ".claude-plugin").mkdir()
    shutil.copy(REPO / bc.MARKETPLACE_REL, root / bc.MARKETPLACE_REL)
    (root / "docs").mkdir()
    shutil.copy(REPO / bc.CATALOG_DOC_REL, root / bc.CATALOG_DOC_REL)
    shutil.copy(REPO / "README.md", root / "README.md")
    return root


def test_check_passes_on_the_repository() -> None:
    assert bc.main(["--check"]) == 0


def test_stale_catalogue_fails_check(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _full_scratch(tmp_path)
    manifest = root / "plugins" / "rf-agentskills" / "catalog.yaml"
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
    names = [e["name"] for e in json.loads((root / bc.MARKETPLACE_REL).read_text())["plugins"]]
    assert names == ["rf-agentskills"]
