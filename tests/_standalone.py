"""Standalone copies of the plugins' skills, as the release tarballs ship them.

The repository keeps one copy of each skill, in ``plugins/<plugin>/skills/``.
Tests about the standalone form (plain ``scripts/x.py`` commands, no
``${CLAUDE_SKILL_DIR}``) read an export made once per test session by
``scripts/export-skills.py``.
"""
from __future__ import annotations

import atexit
import importlib.util
import shutil
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=None)
def standalone_skills(plugin: str = "all") -> Path:
    spec = importlib.util.spec_from_file_location("export_skills", ROOT / "scripts" / "export-skills.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("export_skills", module)
    spec.loader.exec_module(module)
    out = Path(tempfile.mkdtemp(prefix="standalone-skills-"))
    atexit.register(shutil.rmtree, out, ignore_errors=True)
    module.export_plugins(ROOT, plugin, out / "skills")
    return out / "skills"
