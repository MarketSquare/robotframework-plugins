"""Upgrading after a plugin was removed from the catalogue (spec
plugin-lifecycle, "Upgrade cleans up a removed plugin"; launch task 7.2)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from robotframework_plugins import _assets
from robotframework_plugins.cli import main

ROOTS = {"claude-code": ".claude", "codex": ".codex", "cursor": ".cursor", "opencode": ".opencode"}


def _bundle(tmp_path: Path, name: str, *, with_extra: bool) -> Path:
    """The real bundled assets, plus (``with_extra``) a plugin rf-extra with one skill."""
    real = Path(str(_assets.bundle_root_traversable()))
    bundle = tmp_path / name
    shutil.copytree(real, bundle)
    catalog = json.loads((bundle / "catalog.json").read_text())
    if with_extra:
        skill = bundle / "plugins" / "rf-extra" / "skills" / "rf-extra"
        (skill / "references").mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: rf-extra\ndescription: Extra things.\n---\n# Extra\n")
        (skill / "references" / "notes.md").write_text("# Notes\n")
        (bundle / "plugins" / "rf-extra" / ".claude-plugin").mkdir()
        (bundle / "plugins" / "rf-extra" / ".claude-plugin" / "plugin.json").write_text(
            '{"name": "rf-extra", "version": "1.0.0"}')
        catalog["plugins"].append({"name": "rf-extra", "version": "1.0.0", "tier": "community",
                                   "status": "deprecated", "summary": "Extra.", "libraries": []})
    (bundle / "catalog.json").write_text(json.dumps(catalog))
    return bundle


def _install(project: Path, agent: str, *extra: str) -> int:
    return main(["install", "--agent", agent, "--scope", "project", "--project", str(project), "--yes", *extra])


@pytest.mark.parametrize("agent", sorted(ROOTS))
def test_upgrade_cleans_up_a_removed_plugin(agent: str, fake_home: Path, tmp_path: Path,
                                            monkeypatch: pytest.MonkeyPatch,
                                            capsys: pytest.CaptureFixture[str]) -> None:
    before, after = _bundle(tmp_path, "before", with_extra=True), _bundle(tmp_path, "after", with_extra=False)
    project = tmp_path / "proj"
    project.mkdir()
    with monkeypatch.context() as m:
        m.setattr(_assets, "bundle_root_traversable", lambda: before)
        assert _install(project, agent, "--plugins", "rf-core,rf-extra") == 0
    skill_md = next(p for p in project.rglob("SKILL.md") if p.parent.name == "rf-extra")
    notes = skill_md.parent / "references" / "notes.md"
    notes.write_text("# Notes\n\nMy own notes.\n")  # user-modified
    capsys.readouterr()

    with monkeypatch.context() as m:
        m.setattr(_assets, "bundle_root_traversable", lambda: after)
        assert _install(project, agent) == 0
    captured = capsys.readouterr()
    out, err = " ".join(captured.out.split()), " ".join(captured.err.split())
    assert not skill_md.exists()
    assert notes.read_text() == "# Notes\n\nMy own notes.\n"
    assert "plugins rf-extra (no longer in the catalogue)" in out
    assert "notes.md is no longer shipped but was modified by you" in err
    record = json.loads((project / ".rf-agentskills" / "installed.json").read_text())
    tracked = {f["path"] for ins in record["installations"] for f in ins["files"]}
    assert not any("rf-extra" in p for p in tracked)
    assert any(p.parent.name == "rf-language" for p in project.rglob("SKILL.md"))
