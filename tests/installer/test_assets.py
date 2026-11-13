"""Verify the bundled asset tree is reachable at runtime."""

from __future__ import annotations

from robotframework_plugins import _assets


def test_asset_root_exists() -> None:
    with _assets.asset_root_path() as root:
        assert root.is_dir()
        assert (root / "skills").is_dir()
        assert (root / "agents").is_dir()
        assert (root / "hooks" / "hooks.json").is_file()


def test_asset_files_walks_all_categories() -> None:
    files = list(_assets.asset_files())
    assert len(files) > 50, f"expected the full bundle ({len(files)} found)"


def test_asset_files_filtered_by_category() -> None:
    skills = list(_assets.asset_files("skills"))
    agents = list(_assets.asset_files("agents"))
    assert len(skills) > 10
    assert 1 <= len(agents) <= 20
    assert all(f.suffix == ".md" for f in agents)


def test_skill_md_exists_for_known_skill() -> None:
    files = list(_assets.asset_files("skills", "rf-python-library"))
    assert any(f.name == "SKILL.md" for f in files)


# --- catalogue bundle (launch-plugin-programme task 3.3) -------------------

import json  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import zipfile  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


def test_bundle_has_catalog_and_plugin_dir() -> None:
    with _assets.asset_root_path() as root:
        assert root.as_posix().endswith("_assets/plugins/rf-core")
    names = {p["name"]: p for p in _assets.bundled_catalog()}
    assert names["rf-core"]["tier"] == "verified"
    assert names["rf-core"]["version"]
    assert names["rf-agentskills"]["bundle"] is True
    assert _assets.content_plugins() == ("rf-core", "rf-api", "rf-desktop", "rf-mobile", "rf-web")


def test_bundle_leaves_out_plugin_tests_and_evals() -> None:
    with _assets.asset_root_path() as root:
        assert not (root / "tests").exists() and not (root / "evals").exists()
        # Only the plugin's own folders: a skill's example tests/ ship.
        assert (root / "skills" / "rf-language" / "assets" / "examples" / "tests").is_dir()


@pytest.mark.slow
def test_wheel_contains_bundled_plugins(tmp_path: Path) -> None:
    if shutil.which("uv") is None:
        pytest.skip("uv not on PATH")
    subprocess.run(["uv", "build", "--wheel", "-q", "-o", str(tmp_path)], cwd=REPO / "installer", check=True)
    (wheel,) = tmp_path.glob("robotframework_plugins-*.whl")
    names = zipfile.ZipFile(wheel).namelist()
    assert "robotframework_plugins/_assets/catalog.json" in names
    assert "robotframework_plugins/_assets/plugins/rf-agentskills/.claude-plugin/plugin.json" in names
    assert any(n.startswith("robotframework_plugins/_assets/plugins/rf-web/skills/rf-browser/") for n in names)


def test_plan_covers_every_plugin_and_records_it(two_plugin_bundle: Path, install_prefix: Path) -> None:
    from dataclasses import replace

    from robotframework_plugins import cli
    from robotframework_plugins.adapters._base import InstallOptions
    from robotframework_plugins.adapters.claude_code import ClaudeCodeAdapter

    opts = replace(InstallOptions(prefix=install_prefix), plugins=("rf-web", "rf-example"))
    plan = cli._plan_plugins(ClaudeCodeAdapter(), opts)
    by_plugin: dict[str, set[str]] = {}
    for t in plan.targets:
        by_plugin.setdefault(t.plugin, set()).add(t.dst.relative_to(install_prefix).as_posix())
    assert "skills/rf-example/SKILL.md" in by_plugin["rf-example"]
    assert "skills/rf-browser/SKILL.md" in by_plugin["rf-web"]
    # Each plugin's support files live in its own folder.
    assert all(not p.startswith("rf-web-files/") for p in by_plugin["rf-example"])
    assert all(not p.startswith("rf-example-files/") for p in by_plugin["rf-web"])


def test_manifest_records_the_plugin_of_each_file(fake_home: Path, tmp_path: Path) -> None:
    from robotframework_plugins.cli import main

    prefix = tmp_path / "root"
    assert main(["install", "--agent", "claude-code", "--prefix", str(prefix), "--yes"]) == 0
    (path,) = list(tmp_path.rglob("installed.json"))
    data = json.loads(path.read_text())
    files = [f for ins in data["installations"] for f in ins["files"]]
    assert files and {f["plugin"] for f in files} == {"rf-core", "rf-web", "rf-api", "rf-mobile", "rf-desktop"}


def test_installer_ships_the_repository_license() -> None:
    """installer/LICENSE goes into the wheel and sdist; it must stay the repository's LICENSE."""
    assert (REPO / "installer" / "LICENSE").read_bytes() == (REPO / "LICENSE").read_bytes()
