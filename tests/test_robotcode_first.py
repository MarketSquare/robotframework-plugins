"""Tests for scripts/check-robotcode-first.py (spec robotcode-first-tooling,
"Automated guard with a reasoned allowlist")."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytest.importorskip("tomllib")

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check-robotcode-first.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_robotcode_first", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_robotcode_first"] = module
    spec.loader.exec_module(module)
    return module


guard = _load()


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _allow(root: Path, *entries: tuple[str, str]) -> Path:
    body = "".join(f'[[allow]]\nfile = "{f}"\npattern = "{p}"\nreason = "test"\n\n' for f, p in entries)
    return _write(root, "allow.toml", body)


def run(capsys, root: Path, allowlist: Path):
    code = guard.main(["--root", str(root), "--allowlist", str(allowlist)])
    return code, capsys.readouterr().out


def test_repository_passes(capsys):
    code, out = run(capsys, REPO_ROOT, guard.DEFAULT_ALLOWLIST)
    assert code == 0, out


def test_new_reimplementation_fails(capsys, tmp_path):
    _write(tmp_path, "src/pkg/results.py", "from robot.api import ExecutionResult\n")
    code, out = run(capsys, tmp_path, _allow(tmp_path))
    assert code == 1
    assert "src/pkg/results.py:1: execution-result" in out


def test_allowlisted_use_passes(capsys, tmp_path):
    rel = "plugins/rf-core/skills/rf-python-library/scripts/check_library.py"
    _write(tmp_path, rel, "from robot.libdocpkg import LibraryDocumentation\n")
    code, out = run(capsys, tmp_path, _allow(tmp_path, (rel, "libdoc")))
    assert code == 0, out


def test_stale_entry_fails(capsys, tmp_path):
    _write(tmp_path, "scripts/tool.py", "print('nothing to see')\n")
    code, out = run(capsys, tmp_path, _allow(tmp_path, ("scripts/tool.py", "libdoc")))
    assert code == 1
    assert "stale allowlist entry: scripts/tool.py (libdoc)" in out


def test_robocop_is_not_flagged(capsys, tmp_path):
    _write(tmp_path, "plugins/rf-core/scripts/lint.mjs",
           'const r = spawnSync(robocop, ["check", "--select", "DEPR*", file]);\n'
           'spawnSync("robocop", ["format", file]);\n')
    _write(tmp_path, "plugins/rf-core/hooks/run.py", 'subprocess.run(["robocop", "check", path])\n')
    code, out = run(capsys, tmp_path, _allow(tmp_path))
    assert code == 0, out


@pytest.mark.parametrize("line, pattern", [
    ('cmd = ["robot", "--outputdir", out, path]', "run-robot"),
    ('subprocess.run([sys.executable, "-m", "robot", "--dryrun", path])', "run-robot"),
    ('spawnSync(py, ["-m", "robot.libdoc", lib, out]);', "run-robot"),
    ('subprocess.run([uvx, "--from", spec, "rebot", out])', "run-robot"),
    ('binary = shutil.which("robot")', "run-robot"),
    ('candidate = Path(sys.executable).parent / "robot"', "run-robot"),
    ("import xml.etree.ElementTree as ET", "xml-parsing"),
    ("from robot.running.builder import TestSuiteBuilder", "suite-builder"),
    ("model = get_model(str(path))", "parser-model"),
    ("class V(ModelVisitor):", "parser-model"),
    ("doc = LibraryDocumentation(name)", "libdoc"),
])
def test_patterns(capsys, tmp_path, line, pattern):
    _write(tmp_path, "scripts/tool.py", line + "\n")
    code, out = run(capsys, tmp_path, _allow(tmp_path))
    assert code == 1
    assert f"scripts/tool.py:1: {pattern}" in out


@pytest.mark.parametrize("line", [
    'const r = spawnSync("robot", ["--dryrun", file]);',
    'spawnSync(py, ["-m", "robot", "--dryrun", file]);',
])
def test_js_starting_robot_fails(capsys, tmp_path, line):
    _write(tmp_path, "plugins/rf-core/scripts/tool.mjs", line + "\n")
    code, out = run(capsys, tmp_path, _allow(tmp_path))
    assert code == 1
    assert "tool.mjs:1: run-robot" in out


@pytest.mark.parametrize("line", [
    "# parse output.xml with ExecutionResult",
    "// spawn robot with -m robot",
    'hint = "results: robotcode results, not output.xml"',
    'ok = findInterpreterWith("robot", cwd)',
    'importlib.util.find_spec("robot")',
    'run(["robotcode", "robot", "--dryrun", path])',
    'cmd = [robotcode, "robot", "--outputdir", out, path]',
])
def test_prose_comments_and_probes_pass(capsys, tmp_path, line):
    _write(tmp_path, "scripts/tool.py", line + "\n")
    code, out = run(capsys, tmp_path, _allow(tmp_path))
    assert code == 0, out


def test_js_robotcode_subcommand_passes(capsys, tmp_path):
    _write(tmp_path, "plugins/rf-core/scripts/tool.mjs", 'spawnSync(robotcode, ["robot", "--dryrun", file]);\n')
    code, out = run(capsys, tmp_path, _allow(tmp_path))
    assert code == 0, out


def test_paths_outside_tooling_are_not_scanned(capsys, tmp_path):
    _write(tmp_path, "tests/test_x.py", "from robot.api import ExecutionResult\n")
    _write(tmp_path, "installer/src/x.py", "from robot.api import ExecutionResult\n")
    code, out = run(capsys, tmp_path, _allow(tmp_path))
    assert code == 0, out


def test_entry_without_reason_is_rejected(tmp_path):
    allow = _write(tmp_path, "allow.toml", '[[allow]]\nfile = "scripts/x.py"\npattern = "libdoc"\n')
    with pytest.raises(SystemExit, match="lacks reason"):
        guard.main(["--root", str(tmp_path), "--allowlist", str(allow)])
