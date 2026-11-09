"""Gitleaks finds an Anthropic API key (launch task 5.7; the scanner spike's
canary C7 was inconclusive because its fake key had the wrong length).

The key is built at test time so that no key-shaped string is committed.
Runs when Gitleaks is installed (scripts/install-scanners.sh; SCANNERS or
.scanners/bin), and is skipped otherwise.
"""
from __future__ import annotations

import json
import os
import random
import shutil
import string
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _gitleaks() -> str | None:
    installed = Path(os.environ.get("SCANNERS", ROOT / ".scanners" / "bin")) / "gitleaks"
    return str(installed) if installed.is_file() else shutil.which("gitleaks")


def fake_anthropic_key(seed: int = 7) -> str:
    """The shape of Gitleaks' anthropic-api-key rule: sk-ant-api03-, 93 characters, AA."""
    rng = random.Random(seed)
    return "sk-ant-api03-" + "".join(rng.choice(string.ascii_letters + string.digits) for _ in range(93)) + "AA"


@pytest.mark.skipif(_gitleaks() is None, reason="gitleaks not installed (scripts/install-scanners.sh)")
def test_gitleaks_detects_an_anthropic_key(tmp_path: Path) -> None:
    ref = tmp_path / "plugins" / "canary" / "skills" / "canary-skill" / "references" / "notes.md"
    ref.parent.mkdir(parents=True)
    ref.write_text(f"# Notes\n\nexport ANTHROPIC_API_KEY={fake_anthropic_key()}\n", encoding="utf-8")
    report = tmp_path / "report.json"
    res = subprocess.run([_gitleaks(), "dir", str(tmp_path / "plugins"), "--no-banner", "--redact",
                          "--report-format", "json", "--report-path", str(report)],
                         capture_output=True, text=True)
    assert res.returncode == 1, res.stderr
    findings = json.loads(report.read_text())
    assert [(f["RuleID"], Path(f["File"]).name, f["StartLine"]) for f in findings] == [("anthropic-api-key", "notes.md", 3)]
