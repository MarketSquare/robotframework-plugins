"""What the split put where (spec plugin-split): rf-core holds no library recipes,
keyword examples or locators; text names the plugin of a skill it doesn't ship;
migration tables live in the target library skill."""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "plugins" / "rf-core"

_spec = importlib.util.spec_from_file_location("check_plugin_references", ROOT / "scripts" / "check-plugin-references.py")
refs = importlib.util.module_from_spec(_spec)
sys.modules["check_plugin_references"] = refs
_spec.loader.exec_module(refs)

#: Install recipes, keyword examples and locator strategies of a specific library.
LIBRARY_SPECIFIC = re.compile(
    r"rfbrowser (init|install)|Browser\.entry|appium driver install|npm i(nstall)? -g appium"
    r"|uv add [^|`\n]*(robotframework-(browser|seleniumlibrary|appiumlibrary|requests|PlatynUI)|RESTinstance)"
    r"|New Browser|New Page|New Context|Open Browser|Click Element|Fill Text|On Session|Create Session"
    r"|Open Application|Wait Until Element|Wait For Elements State|css=|xpath=|accessibility_id="
)


def _core_files() -> list[Path]:
    skip = {"tests", "evals", "variants", "__pycache__"}
    return [p for p in sorted(CORE.rglob("*")) if p.is_file() and not skip & set(p.relative_to(CORE).parts)]


def _setup_table_rows() -> set[str]:
    """rf-setup's Step 4 library-to-plugin table: the one allowed place."""
    text = (CORE / "skills" / "rf-setup" / "SKILL.md").read_text(encoding="utf-8")
    step4 = text.split("## Step 4", 1)[1].split("\n## ", 1)[0]
    return {ln for ln in step4.splitlines() if ln.startswith("| ")}


def test_library_specific_content_outside_core() -> None:
    allowed = _setup_table_rows()
    hits = []
    for path in _core_files():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for no, line in enumerate(lines, 1):
            if LIBRARY_SPECIFIC.search(line) and line not in allowed:
                hits.append(f"{path.relative_to(ROOT)}:{no}: {line.strip()[:120]}")
    assert not hits, "library-specific content in rf-core:\n" + "\n".join(hits)


def test_the_setup_table_is_the_exception() -> None:
    rows = _setup_table_rows()
    assert any("rfbrowser install" in r for r in rows)


def test_migration_tables_live_in_library_skills() -> None:
    agent = (CORE / "agents" / "rf-migration-guide.md").read_text(encoding="utf-8")
    for row in ("| `Open Browser", "| `GET On Session", "SeleniumLibrary | Browser | Note", "RequestsLibrary | RESTinstance |"):
        assert row not in agent, row
    browser = ROOT / "plugins" / "rf-web" / "skills" / "rf-browser" / "references" / "migrate-from-selenium.md"
    rest = ROOT / "plugins" / "rf-api" / "skills" / "rf-restinstance" / "references" / "migrate-from-requests.md"
    assert "| `Open Browser    ${URL}    chrome` |" in browser.read_text(encoding="utf-8")
    assert "| `GET On Session    api    /path` |" in rest.read_text(encoding="utf-8")
    assert "references/migrate-from-selenium.md" in agent and "references/migrate-from-requests.md" in agent
    assert "`rf-browser` (plugin `rf-web`" in agent and "`rf-restinstance` (plugin `rf-api`" in agent


@pytest.mark.parametrize("agent", ["rf-test-architect", "rf-debug-expert", "rf-migration-guide"])
def test_subagents_suggest_the_missing_plugin(agent: str) -> None:
    text = (CORE / "agents" / f"{agent}.md").read_text(encoding="utf-8")
    assert re.search(r"suggest installing (it|that plugin)", text), agent
    assert "don't continue from memory" in text


# --- cross-plugin reference lint (task 4.2) --------------------------------

def test_repository_passes_the_reference_lint() -> None:
    assert refs.findings(ROOT) == []


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    for plugin, skill in (("rf-core", "rf-setup"), ("rf-mobile", "rf-appium")):
        d = tmp_path / "plugins" / plugin / "skills" / skill
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\nname: {skill}\ndescription: Not installs: rf-setup.\n---\nBody\n")
    return tmp_path


def test_lint_finds_an_unqualified_reference(tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
    agent = tree / "plugins" / "rf-core" / "agents" / "rf-test-architect.md"
    agent.parent.mkdir()
    agent.write_text("| Mobile | `rf-appium` (plugin `rf-mobile`) |\nFor mobile, load `rf-appium`.\n")
    assert refs.main(["--root", str(tree)]) == 1
    out = capsys.readouterr().out.strip().splitlines()
    assert out == ["plugins/rf-core/agents/rf-test-architect.md:2: names rf-appium without its plugin rf-mobile"]


def test_lint_skips_descriptions_changelogs_and_marked_lines(tree: Path) -> None:
    core = tree / "plugins" / "rf-core"
    (core / "CHANGELOG.md").write_text("- moved rf-appium\n")
    (core / "scripts").mkdir()
    (core / "scripts" / "hook.mjs").write_text("const RE = /rf-appium/;  // plugin-ref: ignore\n")
    assert refs.findings(tree) == []
