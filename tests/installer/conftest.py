"""Shared fixtures for installer tests.

Strategy:
* Tests use ``tmp_path`` for both the install destination AND the
  manifest location, so no test ever touches the developer's real
  ``~/.claude/`` or ``~/.local/share/rf-agentskills/``.
* The asset bundle is read from the package's installed location
  (``importlib.resources`` finds it whether we're under pip-install
  or pip-editable mode).
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Repoint ``$HOME`` and the manifest dir at a tempdir.

    Used by tests that exercise install paths with the default user
    scope (no ``--prefix``) so they end up writing inside the tempdir
    instead of the developer's real home.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "share"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))   # Windows
    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData" / "Roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData" / "Local"))
    # Project scope is the default and targets the CWD — chdir into the
    # sandbox so a default-scope install never writes into the real repo.
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def install_prefix(tmp_path: Path) -> Path:
    """A clean per-test install root, used as ``--prefix`` value."""
    p = tmp_path / "install-root"
    p.mkdir()
    return p


@pytest.fixture
def two_plugin_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The real bundled plugins (rf-core, the technology plugins and the
    rf-agentskills bundle, all verified) plus a one-skill community plugin,
    rf-example, and a deprecated one, rf-old."""
    import json
    import shutil

    from robotframework_plugins import _assets

    bundle = tmp_path / "bundle"
    real = _assets.bundle_root_traversable()
    with _assets.as_file(real) as real_dir:
        shutil.copytree(Path(real_dir) / "plugins", bundle / "plugins")
    for name in ("rf-example", "rf-old"):
        skill = bundle / "plugins" / name / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Example.\n---\nBody\n")
        (bundle / "plugins" / name / ".claude-plugin").mkdir()
        (bundle / "plugins" / name / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": name, "version": "1.0.0"}))
    (bundle / "catalog.json").write_text(json.dumps({"plugins": [
        *_assets.bundled_catalog(),
        {"name": "rf-example", "version": "1.0.0", "tier": "community", "status": "active",
         "summary": "A community plugin.", "libraries": []},
        {"name": "rf-old", "version": "1.0.0", "tier": "community", "status": "deprecated",
         "summary": "An old plugin.", "libraries": [], "replacement": "rf-example",
         "deprecated_since": "2026-11-08"},
    ]}))
    monkeypatch.setattr(_assets, "bundle_root_traversable", lambda: bundle)
    return bundle
