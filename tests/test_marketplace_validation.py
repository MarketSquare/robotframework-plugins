"""Tests for marketplace structural integrity."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
PLUGIN_ROOT = ROOT / "plugins" / "rf-agentskills"


def test_marketplace_json_exists():
    assert (ROOT / ".claude-plugin" / "marketplace.json").exists()


def test_marketplace_json_valid():
    with open(ROOT / ".claude-plugin" / "marketplace.json", encoding="utf-8") as f:
        data = json.load(f)
    assert "name" in data
    assert "owner" in data
    assert "plugins" in data
    assert isinstance(data["plugins"], list)
    assert len(data["plugins"]) > 0


def test_plugin_json_exists():
    assert (PLUGIN_ROOT / ".claude-plugin" / "plugin.json").exists()


def test_plugin_json_valid():
    with open(PLUGIN_ROOT / ".claude-plugin" / "plugin.json", encoding="utf-8") as f:
        data = json.load(f)
    assert "name" in data
    assert "version" in data


def test_all_plugin_sources_exist():
    with open(ROOT / ".claude-plugin" / "marketplace.json", encoding="utf-8") as f:
        data = json.load(f)
    for plugin in data["plugins"]:
        source = plugin["source"]
        plugin_dir = ROOT / source
        assert plugin_dir.is_dir(), f"Plugin source missing: {source}"


def test_all_skills_have_skill_md():
    entries = sorted(d for d in ROOT.glob("plugins/*/skills/*") if d.is_dir())
    assert entries
    for entry in entries:
        assert (entry / "SKILL.md").exists(), f"Missing SKILL.md: {entry}"


def test_plugin_names_unique():
    with open(ROOT / ".claude-plugin" / "marketplace.json", encoding="utf-8") as f:
        data = json.load(f)
    names = [p["name"] for p in data["plugins"]]
    assert len(names) == len(set(names)), "Duplicate plugin names found"


def test_skill_md_frontmatter():
    """Delegates to scripts/validate-skills.py so there is one rule set."""
    spec = importlib.util.spec_from_file_location("validate_skills", ROOT / "scripts" / "validate-skills.py")
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    violations = validator.validate(ROOT)
    assert not violations, "\n".join(violations)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_plugin_sets_no_default_main_agent():
    """Enabling a plugin must not replace the user's main agent."""
    for plugin in ROOT.glob("plugins/*/.claude-plugin/plugin.json"):
        assert not (plugin.parent.parent / "settings.json").exists(), plugin
        assert "agent" not in (_json(plugin).get("settings") or {}), plugin


def test_one_claude_format_marketplace_for_every_agent():
    """Copilot, Codex and Cursor read .claude-plugin/; a root plugin.json or
    .cursor-plugin/ manifest would take precedence there and drop hooks/agents."""
    assert not (ROOT / "plugin.json").exists()
    assert not list(ROOT.glob("plugins/*/plugin.json"))
    assert not (ROOT / ".cursor-plugin").exists()
    assert not list(ROOT.glob("plugins/*/.cursor-plugin"))


def test_marketplace_and_plugin_manifests_agree():
    marketplace = _json(ROOT / ".claude-plugin" / "marketplace.json")
    manifest = _json(PLUGIN_ROOT / ".claude-plugin" / "plugin.json")
    [entry] = [p for p in marketplace["plugins"] if p["name"] == manifest["name"]]
    # The bundle installs from its generated copy, which carries the same plugin.json.
    assert entry["source"] == "./bundles/rf-agentskills"
    assert _json(ROOT / "bundles" / "rf-agentskills" / ".claude-plugin" / "plugin.json") == manifest
    for e in marketplace["plugins"]:
        assert _json(ROOT / e["source"] / ".claude-plugin" / "plugin.json")["name"] == e["name"]
    # One version per plugin, only in plugin.json: Claude Code reads it first
    # and warns when an entry disagrees (RELEASING.md, plugin tags <plugin>--v<version>).
    assert manifest["version"]
    assert all("version" not in e for e in marketplace["plugins"])
    assert "version" not in marketplace.get("metadata", {})
    assert not (ROOT / "VERSION").exists()
