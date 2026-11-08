"""CI test selection per plugin (plugin-catalogue: "PR runs only the changed
plugin's tests"), on a scratch tree with a fixture second plugin."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location("select_plugin_tests", ROOT / "scripts" / "select-plugin-tests.py")
sel = importlib.util.module_from_spec(_spec)
sys.modules["select_plugin_tests"] = sel
_spec.loader.exec_module(sel)


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    for plugin in ("rf-agentskills", "rf-example"):
        (tmp_path / "plugins" / plugin / "tests").mkdir(parents=True)
        (tmp_path / "plugins" / plugin / "tests" / "test_x.py").write_text("")
    hook = tmp_path / "plugins" / "rf-agentskills" / "scripts" / "shared.mjs"
    hook.parent.mkdir()
    hook.write_text("")
    return tmp_path


def test_the_real_repository_has_plugin_tests():
    assert "rf-agentskills" in sel.plugins_with_tests(ROOT)
    assert not (ROOT / "tests" / "test_hook_scripts.py").exists()


def test_change_inside_one_plugin_runs_only_that_plugin(tree: Path):
    changed = ["plugins/rf-agentskills/skills/rf-browser/SKILL.md", "plugins/rf-agentskills/tests/test_x.py"]
    assert sel.select(tree, changed) == ["rf-agentskills"]
    assert sel.select(tree, ["plugins/rf-example/catalog.yaml"]) == ["rf-example"]


def test_change_outside_plugins_runs_every_plugin(tree: Path):
    assert sel.select(tree, ["plugins/rf-example/catalog.yaml", "scripts/check-drift.sh"]) == [
        "rf-agentskills", "rf-example"]


def test_no_changed_paths_runs_every_plugin(tree: Path):
    assert sel.select(tree, None) == ["rf-agentskills", "rf-example"]


def test_change_to_a_linked_file_runs_the_linking_plugin(tree: Path):
    link = tree / "plugins" / "rf-example" / "scripts" / "shared.mjs"
    link.parent.mkdir()
    link.symlink_to(Path("../../rf-agentskills/scripts/shared.mjs"))
    assert sel.select(tree, ["plugins/rf-agentskills/scripts/shared.mjs"]) == ["rf-agentskills", "rf-example"]
    assert sel.select(tree, ["plugins/rf-agentskills/skills/rf-browser/SKILL.md"]) == ["rf-agentskills"]


def test_cli_writes_the_github_output(tree: Path, tmp_path: Path, capsys):
    paths = tmp_path / "changed.txt"
    paths.write_text("plugins/rf-agentskills/skills/rf-browser/SKILL.md\n")
    out = tmp_path / "gh.txt"
    assert sel.main(["--root", str(tree), "--paths-file", str(paths), "--github-output", str(out)]) == 0
    assert capsys.readouterr().out.split() == ["rf-agentskills"]
    key, value = out.read_text().strip().split("=", 1)
    assert key == "plugins" and json.loads(value) == ["rf-agentskills"]
