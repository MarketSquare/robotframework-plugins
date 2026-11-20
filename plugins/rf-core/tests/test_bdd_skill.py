"""Structure, content and example checks for the rf-bdd skill (add-rf-bdd-skill, tasks 3.1-3.3).

Layers:

1. Structure (always): frontmatter, H2 order, size budget, the reference set and its
   table, contents lists, no reference-to-reference links, no path into another
   skill, version gate, Step 0 defaults, 11 house rules, gotchas, modes and the
   companion rows.
2. Robot Framework (skipped without ``robot``): every ``robotframework`` code block
   in SKILL.md and the references dry-runs against a copy of ``assets/examples``;
   both example projects dry-run and run for real.
3. Robocop (the installed robocop, and Robocop 9.x through
   ``uvx --from "robotframework-robocop>=9.1,<10"`` when available): the examples
   are clean with ``assets/robocop-bdd.toml``, and every rule ID cited in
   ``references/robocop.md`` exists.

A code block whose first line starts with ``# Wrong`` is a counter-example and is not
run. An HTML comment ``<!-- file: <path> -->`` right above a block says where the block
goes in the example tree: a path starting with ``resource-strategy/``,
``world-strategy/`` or ``sut/`` is relative to ``assets/examples``, any other path is
relative to ``assets/examples/resource-strategy``.
"""

from __future__ import annotations

import functools
import importlib.util
import re
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "plugins" / "rf-core" / "skills" / "rf-bdd"
SKILL_MD = SKILL / "SKILL.md"
REFS = SKILL / "references"
EXAMPLES = SKILL / "assets" / "examples"
ROBOCOP_ASSET = SKILL / "assets" / "robocop-bdd.toml"

HAS_ROBOT = importlib.util.find_spec("robot") is not None
needs_robot = pytest.mark.skipif(not HAS_ROBOT, reason="robotframework not installed")

REQUIRED_SECTIONS = [
    "When to use",
    "Version gate",
    "Step 0: Match the project",
    "House rules",
    "Write a specification",
    "Review a specification",
    "Gherkin input",
    "Gotchas",
    "When to read the references",
    "Companion Skills",
]
REFERENCES = {
    "gherkin-mapping.md",
    "step-design.md",
    "state.md",
    "data-driven.md",
    "documentation-and-tags.md",
    "robocop.md",
    "review-checklist.md",
}
HARD_LIMIT, TARGET = 500, 300
TOC_WINDOW, TOC_THRESHOLD = 15, 100
# Version-gate rows: text that must appear in a row -> minimum RF version.
GATE = {"scope=TEST": "7.0", "BDD prefix": "7.1", "${amount: int}": "7.3", "[Metadata]": "7.5"}
HOUSE_RULE_TERMS = ("robot:private", "one `When`", "Test Template", "`IF`", "Metadata", "Robocop")
GOTCHA_TERMS = ("dry run", "`IF`", "scope=TEST", "__init__.robot", "--select", "DataDriver")
# Projects in assets/examples -> (python-path entries, number of tests).
PROJECTS = {"resource-strategy": (["resources", "../sut"], 8), "world-strategy": (["lib", "../sut"], 2)}
FILE_MARKER_RE = re.compile(r"<!--\s*file:\s*(\S+)\s*-->\s*\n```(?:robotframework|robot)\n(.*?)^```", re.M | re.S)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _body(text: str) -> str:
    return text.split("\n---\n", 1)[1] if text.startswith("---") else text


def _frontmatter(text: str) -> dict:
    yaml = pytest.importorskip("yaml")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, "no frontmatter"
    return yaml.safe_load(m.group(1))


def _h2(text: str) -> list[str]:
    out, fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
        elif not fence and line.startswith("## "):
            out.append(line[3:].strip())
    return out


def _section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}[ \t]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, f"section {heading!r} missing"
    return m.group(1)


def _rows(text: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", s.strip("|"))]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append(cells)
    return rows


def _all_docs() -> list[Path]:
    return [SKILL_MD, *sorted(REFS.glob("*.md"))]


def _blocks(text: str) -> list[tuple[str | None, str]]:
    """Every robotframework block with the file marker above it, if any."""
    marked = {m.start(2): m.group(1) for m in FILE_MARKER_RE.finditer(text)}
    return [
        (marked.get(m.start(1)), m.group(1))
        for m in re.finditer(r"^```(?:robotframework|robot)\n(.*?)^```", text, re.M | re.S)
    ]


def _is_counter_example(block: str) -> bool:
    first = block.lstrip().splitlines()[0] if block.strip() else ""
    return first.startswith("# Wrong")


def _list_items(section: str) -> list[str]:
    return re.findall(r"^(?:- |\d+\. )(.+)$", section, re.M)


# --- 1. structure ----------------------------------------------------------------


def test_frontmatter_and_layout() -> None:
    fm = _frontmatter(_text(SKILL_MD))
    assert fm["name"] == "rf-bdd" == SKILL.name
    assert fm["license"] == "Apache-2.0"
    compat = fm["compatibility"]
    for needle in ("Python 3.8", "robotframework>=7", "robotcode[all]>=2.8"):
        assert needle in compat, needle
    assert fm["metadata"].get("author") and "version" not in fm["metadata"]
    assert "allowed-tools" not in fm
    assert (SKILL / "references").is_dir() and (SKILL / "assets").is_dir()
    assert not (SKILL / "scripts").exists()
    assert not [p for p in SKILL.rglob("*") if p.is_symlink()]


def test_sections_ordered_and_budget() -> None:
    text = _text(SKILL_MD)
    heads = [h for h in _h2(_body(text)) if h in REQUIRED_SECTIONS]
    assert heads == REQUIRED_SECTIONS
    lines = len(text.splitlines())
    assert lines <= HARD_LIMIT, lines
    if lines > TARGET:
        warnings.warn(f"rf-bdd SKILL.md has {lines} lines (target {TARGET})", stacklevel=1)


def test_orientation_and_when_to_use() -> None:
    body = _body(_text(SKILL_MD))
    head = body.split("## When to use", 1)[0].strip().splitlines()
    assert len([line for line in head if line.strip()]) <= 5, head
    assert re.fullmatch(r"Verified against Robot Framework \d+\.\d+(\.\d+)?\.?", head[-1].strip()), head[-1]
    lines = body.lstrip("\n").splitlines()
    idx = next(i for i, line in enumerate(lines) if line.strip() == "## When to use")
    assert idx < 20, idx
    block = _section(body, "When to use")
    for needle in ("rf-language", "relies on `rf-language`", "`robotcode` skill of the robotcode plugin"):
        assert needle in block, needle


def test_reference_set_matches_table() -> None:
    assert {p.name for p in REFS.glob("*.md")} == REFERENCES
    table = _section(_text(SKILL_MD), "When to read the references")
    named = {m for cells in _rows(table) for m in re.findall(r"references/([a-z-]+\.md)", cells[0])}
    assert named == REFERENCES
    for cells in _rows(table)[1:]:
        assert len(cells) >= 2 and cells[1], cells


def test_references_are_shallow() -> None:
    for ref in sorted(REFS.glob("*.md")):
        text = _text(ref)
        assert not re.search(r"\]\((?!https?:)[^)]*\.md", text), f"{ref.name} links to another file"
        assert "references/" not in text, f"{ref.name} names another reference by path"
        lines = text.splitlines()
        if len(lines) > TOC_THRESHOLD:
            heads = [h for h in _h2(text)]
            window = "\n".join(lines[:TOC_WINDOW])
            missing = [h for h in heads if h not in window]
            assert not missing, f"{ref.name}: contents list lacks {missing}"


def test_no_path_into_another_skill() -> None:
    for doc in [*_all_docs(), *EXAMPLES.rglob("*.*")]:
        if doc.suffix not in {".md", ".robot", ".resource", ".py", ".toml"}:
            continue
        text = _text(doc)
        assert not re.search(r"skills/rf-(?!bdd\b)|\.\./rf-[a-z-]+/", text), doc
        assert "CLAUDE_SKILL_DIR" not in text or doc == SKILL_MD, doc


def test_version_gate() -> None:
    gate = _section(_text(SKILL_MD), "Version gate")
    rows = _rows(gate)
    for feature, version in GATE.items():
        hit = [r for r in rows if feature in r[0]]
        assert hit, feature
        assert hit[0][1] == version, (feature, hit[0])
    assert r"${amount:\d+}" in gate and "Convert To Integer" in gate


def test_step_0_conventions_first() -> None:
    step0 = _section(_text(SKILL_MD), "Step 0: Match the project")
    for needle in ("Title Case", "python-path", "World library", "robotcode doc keywords",
                   "robotcode discover tags", "assets/robocop-bdd.toml", "first word capitalized",
                   "no convention", "rf-language"):
        assert needle in step0, needle


def test_house_rules() -> None:
    rules = _section(_text(SKILL_MD), "House rules")
    numbered = re.findall(r"^(\d+)\. \*\*", rules, re.M)
    assert numbered == [str(i) for i in range(1, 12)], numbered
    for term in HOUSE_RULE_TERMS:
        assert term in rules, term
    assert rules.count("*Why:*") == 11


def test_modes() -> None:
    text = _text(SKILL_MD)
    write = _section(text, "Write a specification")
    for needle in ("robotcode analyze code", "--dryrun", 'robotcode robot -bl "<longname>"', "robocop check",
                   "Report"):
        assert needle in write, needle
    review = _section(text, "Review a specification")
    assert "references/review-checklist.md" in review and "Don't edit files" in review
    assert re.search(r"`ID — file:line — [^`]+`", review)
    gherkin = _section(text, "Gherkin input")
    for needle in (".feature", "parser", "every rule and every example", "1 days", "wording change"):
        assert needle in gherkin, needle


def test_gotchas() -> None:
    gotchas = _section(_text(SKILL_MD), "Gotchas")
    items = _list_items(gotchas)
    assert len(items) >= 11, len(items)
    for term in GOTCHA_TERMS:
        assert term in gotchas, term


def test_companion_skills() -> None:
    text = _text(SKILL_MD)
    assert _h2(_body(text))[-1] == "Companion Skills"
    section = _section(text, "Companion Skills")
    skills = {c for cells in _rows(section) for c in re.findall(r"`(rf-[a-z-]+)`", cells[-1])}
    assert {"rf-language", "rf-setup", "rf-python-library"} <= skills
    assert "`robotcode` skill of the robotcode plugin" in section


def test_documented_robocop_commands_disable_the_cache() -> None:
    """A documented `robocop check` or `format` run must not leave .robocop_cache/ behind."""
    for doc in _all_docs():
        for line in _text(doc).splitlines():
            for cmd in re.findall(r"robocop (?:check|format)\b[^`\n]*", line):
                if cmd.strip() in ("robocop check", "robocop format"):
                    continue  # the bare tool name in prose, not a command to run
                assert "--no-cache" in cmd, f"{doc.name}: {cmd}"


def test_examples_are_library_neutral() -> None:
    forbidden = re.compile(r"^(Library|Resource)\s+(Browser|SeleniumLibrary|RequestsLibrary|REST|AppiumLibrary)\b",
                           re.M)
    for path in EXAMPLES.rglob("*"):
        if path.suffix in {".robot", ".resource"}:
            assert not forbidden.search(_text(path)), path
    for path in EXAMPLES.rglob("*.robot"):
        assert "[Metadata]" not in _text(path), f"{path}: test-level [Metadata] needs RF 7.5"


# --- 2. Robot Framework layer ---------------------------------------------------


def _robot(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "robot", *args], capture_output=True, text=True, timeout=300, cwd=cwd,
    )


def _pythonpath(project: str) -> list[str]:
    return [a for p in PROJECTS[project][0] for a in ("--pythonpath", p)]


@pytest.fixture()
def example_copy(tmp_path: Path) -> Path:
    dest = tmp_path / "examples"
    shutil.copytree(EXAMPLES, dest, ignore=shutil.ignore_patterns("__pycache__", ".robocop_cache", "results"))
    return dest


def _place(marker: str | None, block: str, root: Path, idx: int) -> tuple[str, Path]:
    """Write a block into the example copy; return (project, file or folder to dry-run)."""
    if marker:
        first = marker.split("/", 1)[0]
        rel = marker if first in (*PROJECTS, "sut") else f"resource-strategy/{marker}"
        project = rel.split("/", 1)[0] if rel.split("/", 1)[0] in PROJECTS else "resource-strategy"
        path = root / rel
    else:
        project = "resource-strategy"
        name = "resources" if "*** Test Cases ***" not in block and "*** Keywords ***" in block else "tests"
        path = root / project / name / f"snippet_{idx}.{'resource' if name == 'resources' else 'robot'}"
        if "*** Test Cases ***" not in block and "*** Keywords ***" not in block:
            path = root / project / "tests" / f"snippet_{idx}" / "__init__.robot"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(block, encoding="utf-8")
    if path.suffix == ".resource":
        wrapper = root / project / "tests" / f"wrapper_{idx}.robot"
        wrapper.write_text(
            f"*** Settings ***\nResource    {path.as_posix()}\n\n*** Test Cases ***\nImport only\n    No Operation\n",
            encoding="utf-8",
        )
        return project, wrapper
    if path.name == "__init__.robot":
        (path.parent / "child.robot").write_text(
            "*** Settings ***\nResource    cash_withdrawal_steps.resource\n\n"
            "*** Test Cases ***\nChild\n    No Operation\n",
            encoding="utf-8",
        )
        return project, path.parent
    return project, path


BLOCK_PARAMS = [
    pytest.param(marker, i, block, id=f"{doc.name}-{i}")
    for doc in _all_docs()
    for i, (marker, block) in enumerate(_blocks(_text(doc)))
    if not _is_counter_example(block)
]


@needs_robot
@pytest.mark.parametrize(("marker", "idx", "block"), BLOCK_PARAMS)
def test_code_block_dry_runs(marker: str | None, idx: int, block: str, example_copy: Path) -> None:
    project, target = _place(marker, block, example_copy, idx)
    cwd = example_copy / project
    res = _robot(["--dryrun", *_pythonpath(project), "--outputdir", str(example_copy / "out"), str(target)], cwd)
    log = res.stdout + res.stderr
    assert res.returncode == 0 and "[ ERROR ]" not in log, log


@needs_robot
@pytest.mark.parametrize("project", sorted(PROJECTS))
def test_examples_dry_run_and_run(project: str, example_copy: Path) -> None:
    from robot.api import ExecutionResult

    cwd = example_copy / project
    out = example_copy / "out"
    for extra in (["--dryrun"], []):
        res = _robot([*extra, *_pythonpath(project), "--outputdir", str(out), "tests"], cwd)
        log = res.stdout + res.stderr
        assert res.returncode == 0 and "[ ERROR ]" not in log and "[ WARN ]" not in log, log
        stats = ExecutionResult(str(out / "output.xml")).statistics.total
        assert stats.passed == PROJECTS[project][1] and stats.failed == 0, log


@needs_robot
@pytest.mark.parametrize("project", sorted(PROJECTS))
def test_examples_pass_robotcode_analyze(project: str, example_copy: Path) -> None:
    robotcode = shutil.which("robotcode", path=str(Path(sys.executable).parent)) or shutil.which("robotcode")
    if not robotcode:
        pytest.skip("robotcode not installed")
    res = subprocess.run([robotcode, "analyze", "code"], capture_output=True, text=True, timeout=300,
                         cwd=example_copy / project)
    assert res.returncode == 0 and re.search(r"Errors: 0, Warnings: 0", res.stdout), res.stdout + res.stderr


# --- 3. Robocop layer -----------------------------------------------------------


@functools.lru_cache(maxsize=1)
def _robocop_cmds() -> tuple[tuple[str, ...], ...]:
    """The installed robocop and Robocop 9.x through uvx, those that answer --version."""
    candidates: list[tuple[str, ...]] = []
    local = shutil.which("robocop", path=str(Path(sys.executable).parent)) or shutil.which("robocop")
    if local:
        candidates.append((local,))
    uvx = shutil.which("uvx")
    if uvx:
        candidates.append((uvx, "--from", "robotframework-robocop>=9.1,<10", "robocop"))
    found, majors = [], set()
    for cmd in candidates:
        try:
            res = subprocess.run([*cmd, "--version"], capture_output=True, text=True, timeout=300)
        except (OSError, subprocess.TimeoutExpired):
            continue
        m = re.search(r"(\d+)\.\d+", res.stdout + res.stderr)
        if res.returncode == 0 and m and m.group(1) not in majors:
            majors.add(m.group(1))
            found.append(cmd)
    return tuple(found)


def _robocop_param(index: int) -> tuple[str, ...]:
    cmds = _robocop_cmds()
    if index >= len(cmds):
        pytest.skip("robocop not available in this version")
    return cmds[index]


@pytest.mark.parametrize("index", [0, 1], ids=["installed", "robocop-9"])
@pytest.mark.parametrize("project", sorted(PROJECTS))
def test_examples_are_clean_with_the_asset(index: int, project: str, example_copy: Path) -> None:
    cmd = _robocop_param(index)
    cwd = example_copy / project
    # Lint with the asset only, not the example's own robot.toml.
    (cwd / "robot.toml").unlink()
    shutil.copy(ROBOCOP_ASSET, cwd / "pyproject.toml")
    res = subprocess.run([*cmd, "check", "--no-cache", "."], capture_output=True, text=True, timeout=300, cwd=cwd)
    found = re.findall(r"\b(NAME02|NAME18|VAR06)\b", res.stdout)
    assert not found, res.stdout + res.stderr


@pytest.mark.parametrize("index", [0, 1], ids=["installed", "robocop-9"])
def test_asset_format_settings_load(index: int, example_copy: Path) -> None:
    """`robocop format` accepts the asset: a setting one version doesn't know stops it."""
    cmd = _robocop_param(index)
    cwd = example_copy / "resource-strategy"
    (cwd / "robot.toml").unlink()
    shutil.copy(ROBOCOP_ASSET, cwd / "pyproject.toml")
    res = subprocess.run([*cmd, "format", "--no-cache", "--check", "--diff", "tests"],
                         capture_output=True, text=True, timeout=300, cwd=cwd)
    log = res.stdout + res.stderr
    assert "Error" not in log and "Failed to import" not in log, log


def test_example_configs_carry_the_asset_settings() -> None:
    asset = _text(ROBOCOP_ASSET)
    settings = re.findall(r'^\s*["\']([^"\']+=[^"\']+)["\'],?$', asset, re.M)
    assert settings
    for project in PROJECTS:
        config = _text(EXAMPLES / project / "robot.toml")
        for setting in settings:
            assert setting in config, (project, setting)


@pytest.mark.parametrize("index", [0, 1], ids=["installed", "robocop-9"])
def test_cited_rule_ids_exist(index: int) -> None:
    cmd = _robocop_param(index)
    res = subprocess.run([*cmd, "list", "rules"], capture_output=True, text=True, timeout=300)
    known = set(re.findall(r"\b([A-Z]{2,6}\d{2})\b", res.stdout))
    assert known, res.stdout + res.stderr
    cited = set(re.findall(r"\b([A-Z]{2,6}\d{2})\b", _text(REFS / "robocop.md") + _text(SKILL_MD)))
    assert cited <= known, sorted(cited - known)
