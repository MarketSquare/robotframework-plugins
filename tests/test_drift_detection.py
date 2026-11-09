"""The drift check over plugins/<name>/ (skill-catalog, skill-metadata-conformance
and agent-variants specs), and the standalone export that replaced the root
skills/ copy (plugin-catalogue: each plugin owns its sources)."""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from _shell import BASH, requires_posix_bash

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_SCRIPTS = ROOT / "plugins" / "rf-core" / "scripts"
PLUGIN_SKILLS = ROOT / "plugins" / "rf-core" / "skills"

_spec = importlib.util.spec_from_file_location("export_skills", ROOT / "scripts" / "export-skills.py")
export = importlib.util.module_from_spec(_spec)
sys.modules["export_skills"] = export
_spec.loader.exec_module(export)


def test_no_root_skills_copy_and_no_sync_script():
    assert not (ROOT / "skills").exists()
    assert not (ROOT / "scripts" / "sync-skills.sh").exists()


def test_no_flat_plugin_python_scripts():
    """Scripts ship per skill; the plugin scripts/ dir holds only hook .mjs files."""
    flat = sorted(p.name for p in PLUGIN_SCRIPTS.glob("*.py"))
    assert not flat, f"flat plugin scripts must not exist: {flat}"
    assert all(p.suffix == ".mjs" for p in PLUGIN_SCRIPTS.iterdir() if p.is_file())


def test_skill_dirs_use_rf_names():
    names = {p.name for p in ROOT.glob("plugins/*/skills/*") if p.is_dir()}
    assert names and all(name.startswith("rf-") for name in names), names


# --- standalone export ------------------------------------------------------

def test_export_all_takes_every_plugin(tmp_path: Path):
    names = export.export_plugins(ROOT, "all", tmp_path / "out")
    assert sorted(names) == sorted(p.parent.name for p in ROOT.glob("plugins/*/skills/*/SKILL.md"))
    assert (tmp_path / "out" / "rf-browser" / "SKILL.md").is_file()


def test_export_writes_the_standalone_command_form(tmp_path: Path):
    names = export.export_skills(PLUGIN_SKILLS, tmp_path / "out")
    assert len(names) == len([p for p in PLUGIN_SKILLS.iterdir() if (p / "SKILL.md").is_file()])
    text = (tmp_path / "out" / "rf-python-library" / "SKILL.md").read_text()
    assert "${CLAUDE_SKILL_DIR}" not in text
    assert "uv run python scripts/check_library.py" in text
    assert (tmp_path / "out" / "rf-python-library" / "scripts" / "check_library.py").is_file()
    assert not list((tmp_path / "out").rglob("__pycache__"))


def test_export_only_rewrites_script_commands():
    md = ('Run `uv run python "${CLAUDE_SKILL_DIR}/scripts/check_library.py" Lib`.\n'
          "Keep ${CLAUDE_SKILL_DIR}/assets.\n")
    assert export.standalone_skill_md(md) == (
        "Run `uv run python scripts/check_library.py Lib`.\nKeep ${CLAUDE_SKILL_DIR}/assets.\n")


# --- check-drift.sh ---------------------------------------------------------

@pytest.fixture
def scratch_repo(tmp_path: Path) -> Path:
    """A minimal copy of the repo tree the drift script operates on."""
    dst = tmp_path / "repo"
    shutil.copytree(ROOT / "scripts", dst / "scripts")
    shutil.copytree(ROOT / "plugins", dst / "plugins", ignore=shutil.ignore_patterns("__pycache__"))
    return dst


def _drift(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [BASH, str(repo / "scripts" / "check-drift.sh")],
        capture_output=True, text=True, env={"REPO_ROOT": str(repo), "PATH": "/usr/bin:/bin"},
    )


@requires_posix_bash
def test_drift_check_clean_tree_passes(scratch_repo: Path):
    res = _drift(scratch_repo)
    assert res.returncode == 0, res.stdout + res.stderr


@requires_posix_bash
def test_drift_check_names_flat_plugin_script(scratch_repo: Path):
    (scratch_repo / "plugins/rf-core/scripts/retired_helper.py").write_text("orphan\n")
    res = _drift(scratch_repo)
    assert res.returncode == 1, res.stdout
    assert "ORPHAN: plugins/rf-core/scripts/retired_helper.py" in res.stdout


@requires_posix_bash
@pytest.mark.parametrize(
    "tree",
    [
        "plugins/rf-core/skills/rf-python-library",
        "plugins/rf-core/skills/rf-python-library/scripts",
        "plugins/rf-core/scripts",
    ],
)
def test_drift_check_rejects_symlinks(scratch_repo: Path, tree: str):
    link = scratch_repo / tree / "linked.md"
    link.symlink_to(scratch_repo / "plugins/rf-core/skills/rf-python-library/SKILL.md")
    res = _drift(scratch_repo)
    assert res.returncode == 1, res.stdout
    assert f"SYMLINK: {tree}/linked.md" in res.stdout


@requires_posix_bash
def test_drift_check_rejects_name_dir_mismatch(scratch_repo: Path):
    md = scratch_repo / "plugins/rf-core/skills/rf-language/SKILL.md"
    md.write_text(md.read_text().replace("name: rf-language", "name: language", 1))
    res = _drift(scratch_repo)
    assert res.returncode == 1
    assert "NAME MISMATCH: plugins/rf-core/skills/rf-language/SKILL.md" in res.stdout


@requires_posix_bash
def test_drift_check_covers_every_plugin(scratch_repo: Path):
    skill = scratch_repo / "plugins/rf-example/skills/rf-example"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: rf-wrong\n---\n")
    res = _drift(scratch_repo)
    assert res.returncode == 1
    assert "NAME MISMATCH: plugins/rf-example/skills/rf-example/SKILL.md" in res.stdout


@requires_posix_bash
def test_drift_check_catches_stale_variant(scratch_repo: Path):
    variant = next((scratch_repo / "plugins/rf-core/variants/codex/agents").glob("*.toml"))
    variant.write_text(variant.read_text() + "\n# hand edit\n")
    res = _drift(scratch_repo)
    assert res.returncode == 1, res.stdout


def _append_line(repo: Path, rel: str, line: str) -> None:
    md = repo / rel
    md.write_text(md.read_text() + "\n" + line + "\n")


@requires_posix_bash
@pytest.mark.parametrize(
    ("rel", "line", "expected"),
    [
        ("plugins/rf-core/skills/rf-language/SKILL.md", "python scripts/rf_conventions.py --output output.xml",
         "BARE PYTHON: plugins/rf-core/skills/rf-language/SKILL.md"),
        ("plugins/rf-core/skills/rf-python-library/SKILL.md",
         'python "${CLAUDE_SKILL_DIR}/scripts/check_library.py" --library X',
         "BARE PYTHON: plugins/rf-core/skills/rf-python-library/SKILL.md"),
        ("plugins/rf-core/skills/rf-language/SKILL.md",
         'python3 "${CLAUDE_PLUGIN_ROOT}/scripts/rf_conventions.py" --output output.xml',
         "PLUGIN_ROOT IN SKILL.md: plugins/rf-core/skills/rf-language/SKILL.md"),
        ("plugins/rf-core/skills/rf-setup/SKILL.md", "See ${CLAUDE_PLUGIN_ROOT}/scripts.",
         "PLUGIN_ROOT IN SKILL.md: plugins/rf-core/skills/rf-setup/SKILL.md"),
    ],
)
def test_drift_check_rejects_wrong_command_form(scratch_repo: Path, rel: str, line: str, expected: str):
    _append_line(scratch_repo, rel, line)
    res = _drift(scratch_repo)
    assert res.returncode == 1, res.stdout
    assert expected in res.stdout


@requires_posix_bash
def test_drift_check_accepts_project_env_command_forms(scratch_repo: Path):
    for line in (
        'uv run python "${CLAUDE_SKILL_DIR}/scripts/rf_conventions.py" --output output.xml',
        '`.venv/bin/python "${CLAUDE_SKILL_DIR}/scripts/rf_conventions.py" …` or '
        '`poetry run python "${CLAUDE_SKILL_DIR}/scripts/rf_conventions.py" …`',
    ):
        _append_line(scratch_repo, "plugins/rf-core/skills/rf-language/SKILL.md", line)
    res = _drift(scratch_repo)
    assert res.returncode == 0, res.stdout
