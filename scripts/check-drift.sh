#!/usr/bin/env bash
# Check that every plugin's generated and shipped files are consistent.
# Exit 1 if anything is stale or out of place.
#
# Each plugins/<name>/ is the only source of its content (no root copy):
#   * generated Codex/OpenCode variants match their source subagents;
#   * skill directory names equal their SKILL.md `name:`;
#   * no symbolic links in skill trees or plugin scripts;
#   * no flat plugins/<name>/scripts/*.py (scripts ship per skill);
#   * SKILL.md runs bundled scripts through the project environment.
#
# REPO_ROOT can be overridden (used by tests to run against a scratch tree).
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
# Python and a root path it can open: on Windows (Git Bash) python3 may not
# exist and /d/a/... paths are not valid for a native Windows Python.
PY="$(command -v python3 || command -v python)"
if command -v cygpath >/dev/null 2>&1; then PY_ROOT="$(cygpath -m "$REPO_ROOT")"; else PY_ROOT="$REPO_ROOT"; fi
DRIFT_FOUND=0

# ── Names: skill directory == SKILL.md name ───────────────────────────────
echo "=== Checking skill names ==="
NAMES_OK=1
for skill_dir in "$REPO_ROOT"/plugins/*/skills/*/; do
    [ -d "$skill_dir" ] || continue
    name=$(basename "$skill_dir")
    rel="${skill_dir#"$REPO_ROOT"/}"
    rf_name=$(head -5 "$skill_dir/SKILL.md" 2>/dev/null | grep "^name:" | sed 's/^name: *//' || true)
    if [ "$rf_name" != "$name" ]; then
        echo "NAME MISMATCH: ${rel}SKILL.md has name: '$rf_name'"
        NAMES_OK=0
        DRIFT_FOUND=1
    fi
done
[ $NAMES_OK -eq 1 ] && echo "  OK: names match their directories"

# ── Symlinks: no symbolic link may exist in any skill tree ──────────────────
echo ""
echo "=== Checking for symlinks in skill trees ==="
SYMLINKS=0
for tree in "$REPO_ROOT"/plugins/*/skills "$REPO_ROOT"/plugins/*/scripts; do
    [ -d "$tree" ] || continue
    while IFS= read -r link; do
        echo "SYMLINK: ${link#"$REPO_ROOT"/}"
        SYMLINKS=1
    done < <(find "$tree" -type l | sort)
done
if [ $SYMLINKS -eq 1 ]; then
    DRIFT_FOUND=1
else
    echo "  OK: no symlinks"
fi

# ── Orphans: scripts ship per skill; a flat plugin scripts/*.py is stale ───
echo ""
echo "=== Checking for flat plugin scripts ==="
ORPHANS=0
for plugin_script in "$REPO_ROOT"/plugins/*/scripts/*.py; do
    [ -f "$plugin_script" ] || continue
    echo "ORPHAN: ${plugin_script#"$REPO_ROOT"/} (scripts ship in skills/<skill>/scripts/)"
    ORPHANS=1
done
if [ $ORPHANS -eq 1 ]; then
    DRIFT_FOUND=1
else
    echo "  OK: no flat plugin scripts"
fi

# ── Command form: how SKILL.md files run bundled scripts ───────────────────
# No ${CLAUDE_PLUGIN_ROOT} in any SKILL.md (not expanded for every agent);
# no bare `python scripts/…` / `python3 scripts/…` (runs whatever python is on
# PATH instead of the project environment). Allowed prefixes: `uv run python`,
# `poetry run python`, a venv interpreter path (`.venv/bin/python`).
echo ""
echo "=== Checking script command form in SKILL.md ==="
FORM_OUT=$(REPO_ROOT="$PY_ROOT" "$PY" - <<'PY'
import os, re, sys
from pathlib import Path
root = Path(os.environ["REPO_ROOT"])
bare = re.compile(r"(?<![\w/.\\-])python3? +(?:\"?\$\{CLAUDE_SKILL_DIR\}/)?scripts/")
bad = 0
for md in sorted(root.glob("plugins/*/skills/*/SKILL.md")):
    rel = md.relative_to(root)
    for no, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
        if "${CLAUDE_PLUGIN_ROOT}" in line:
            print(f"PLUGIN_ROOT IN SKILL.md: {rel}:{no}")
            bad = 1
        for m in bare.finditer(line):
            before = line[: m.start()].rstrip()
            if before.endswith(" run") or before.endswith("`run") or before == "run":
                continue
            print(f"BARE PYTHON: {rel}:{no}: {line.strip()}")
            bad = 1
sys.exit(bad)
PY
) && FORM_RC=0 || FORM_RC=$?
if [ -n "$FORM_OUT" ]; then echo "$FORM_OUT"; fi
if [ $FORM_RC -ne 0 ]; then
    DRIFT_FOUND=1
else
    echo "  OK: script commands use the project environment"
fi

echo ""
echo "=== Checking per-agent variants ==="
if "$PY" "$REPO_ROOT/scripts/build-agent-variants.py" --check; then
    :
else
    DRIFT_FOUND=1
fi

echo ""
if [ $DRIFT_FOUND -eq 1 ]; then
    echo "DRIFT DETECTED! Regenerate variants with: python scripts/build-agent-variants.py"
    exit 1
else
    echo "All files in sync."
    exit 0
fi
