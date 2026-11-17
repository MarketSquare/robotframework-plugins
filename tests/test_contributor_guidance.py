"""The AI policy, the agent guide and the templates stay true to CI (spec
contributor-guidance; change ai-contributor-docs, design D4)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(rel: str, root: Path = ROOT) -> str:
    return (root / rel).read_text(encoding="utf-8")


def _section(md: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", md, re.M | re.S)
    assert m, f"AGENTS.md has no '## {heading}' section"
    return m.group(1)


def _squash(text: str) -> str:
    """Whitespace and quotes don't matter when matching a command against CI."""
    return re.sub(r"\s+", " ", text.replace('"', "").replace("'", "")).strip()


def check_commands(root: Path = ROOT) -> list[str]:
    """Commands in the Checks bullets that ci.yml doesn't run."""
    ci = _squash(_text(".github/workflows/ci.yml", root))
    missing = []
    for cmd in re.findall(r"^- `([^`]+)`", _section(_text("AGENTS.md", root), "Checks"), re.M):
        # A placeholder such as <name> stands for one shell word ($plugin in CI).
        parts = re.split(r"<[^>]+>", _squash(cmd))
        if not re.search(r"\S+".join(re.escape(p) for p in parts), ci):
            missing.append(cmd)
    return missing


def missing_scripts(root: Path = ROOT) -> list[str]:
    named = set(re.findall(r"(?<![\w/.])scripts/[\w./-]+\.(?:py|sh)", _text("AGENTS.md", root)))
    return sorted(p for p in named if not (root / p).is_file())


def test_the_documents_exist() -> None:
    for name in ("AGENTS.md", "AI_POLICY.md", "CLAUDE.md"):
        assert (ROOT / name).is_file(), name


def test_every_script_in_the_guide_exists() -> None:
    assert missing_scripts() == []


def test_every_check_runs_in_ci() -> None:
    assert check_commands() == []


def test_claude_md_imports_the_guide() -> None:
    assert [line for line in _text("CLAUDE.md").splitlines() if line.strip()] == ["@AGENTS.md"]


def test_the_policy_is_linked_and_states_robotcode_first() -> None:
    for doc in ("README.md", "CONTRIBUTING.md", "AGENTS.md"):
        assert "AI_POLICY.md" in _text(doc), doc
    for doc in ("AI_POLICY.md", "AGENTS.md"):
        text = _text(doc)
        assert "https://robotcode.io/guides/cli/" in text and "upstream" in text.lower(), doc


def test_the_guide_maps_every_robotcode_capability() -> None:
    table = _section(_text("AGENTS.md"), "RobotCode first")
    for cmd in ("robotcode robot", "robotcode discover", "robotcode analyze code", "robotcode results",
                "robotcode repl", "robotcode robot-debug", "robotcode doc keyword", "robotcode --wrapper",
                "robotcode config", "robotcode profiles"):
        assert f"`{cmd}" in table, cmd


def test_templates_ask_about_ai_and_robotcode() -> None:
    pr = _text(".github/pull_request_template.md")
    assert "## AI assistance" in pr
    assert "Robot Framework capabilities go through `robotcode`; gaps are reported upstream" in pr
    assert "AI tool wrote this report" in _text(".github/ISSUE_TEMPLATE/plugin-feedback.yml")


# --- the checks fail when the guide drifts (task 5.1) ------------------------

def _copy(tmp_path: Path) -> Path:
    for rel in ("AGENTS.md", ".github/workflows/ci.yml"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(_text(rel), encoding="utf-8")
    for script in re.findall(r"(?<![\w/.])scripts/[\w./-]+\.(?:py|sh)", _text("AGENTS.md")):
        (tmp_path / script).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / script).touch()
    return tmp_path


def test_a_renamed_script_is_named(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    (root / "scripts" / "check-drift.sh").unlink()
    assert missing_scripts(root) == ["scripts/check-drift.sh"]


def test_a_check_dropped_from_ci_is_named(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    ci = root / ".github/workflows/ci.yml"
    ci.write_text(ci.read_text().replace("python scripts/check-docs-voice.py", "true"), encoding="utf-8")
    assert check_commands(root) == ["python scripts/check-docs-voice.py"]
