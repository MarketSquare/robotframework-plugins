#!/usr/bin/env bash
# Usage: ./scripts/bump-version.sh [--rc] <major|minor|patch>
# Bumps the one release version (spec release-train; RELEASING.md) that every
# plugin and the installer share:
#   * installer/pyproject.toml, the only place it is written by hand, and the
#     installer's entry in uv.lock;
#   * the generated copies, by running scripts/build-catalog.py (every
#     plugin.json, the installer's __version__, the README and docs/catalog.md);
#   * CHANGELOG.md: "## Unreleased" becomes "## <version> — <date>", under a new,
#     empty "## Unreleased".
# --rc starts a release candidate (5.0.0 with --rc minor gives 5.1.0rc1) or
# advances one (5.1.0rc1 gives 5.1.0rc2). Without --rc, a candidate is finished
# (5.1.0rc1 gives 5.1.0, whichever part is named).
#
# REPO_ROOT can be overridden (used by tests to run against a scratch tree).
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
# Python and a root path it can open: on Windows (Git Bash) python3 may not
# exist and /d/a/... paths are not valid for a native Windows Python.
PY="$(command -v python3 || command -v python)"
if command -v cygpath >/dev/null 2>&1; then PY_ROOT="$(cygpath -m "$REPO_ROOT")"; else PY_ROOT="$REPO_ROOT"; fi

usage() { echo "Usage: $0 [--rc] <major|minor|patch>" >&2; exit 1; }
RC=""
if [ "${1:-}" = "--rc" ]; then RC=1; shift; fi
[ $# -eq 1 ] || usage
case "$1" in major|minor|patch) ;; *) usage ;; esac

NEW=$("$PY" - "$PY_ROOT" "$1" "$RC" <<'PY'
import datetime
import re
import sys
from pathlib import Path

root, part, rc = Path(sys.argv[1]), sys.argv[2], bool(sys.argv[3])
pyproject = root / "installer" / "pyproject.toml"
text = pyproject.read_text(encoding="utf-8")
m = re.search(r'^version = "(\d+)\.(\d+)\.(\d+)(?:rc(\d+))?"$', text, re.M)
if not m:
    sys.exit(f"ERROR: {pyproject.relative_to(root)} has no MAJOR.MINOR.PATCH[rcN] version")
major, minor, patch = (int(m.group(i)) for i in (1, 2, 3))
cand = int(m.group(4)) if m.group(4) else None
current = m.group(0).split('"')[1]
if cand is not None:
    new = f"{major}.{minor}.{patch}rc{cand + 1}" if rc else f"{major}.{minor}.{patch}"
else:
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    new = f"{major}.{minor}.{patch}" + ("rc1" if rc else "")
pyproject.write_text(text[:m.start()] + f'version = "{new}"' + text[m.end():], encoding="utf-8")
print(f"  installer/pyproject.toml: {current} -> {new}", file=sys.stderr)

lock = root / "uv.lock"
if lock.is_file():
    ltext = lock.read_text(encoding="utf-8")
    ltext, n = re.subn(r'(\[\[package\]\]\nname = "robotframework-plugins"\nversion = ")[^"]*(")',
                       lambda mm: mm.group(1) + new + mm.group(2), ltext, count=1)
    if n:
        lock.write_text(ltext, encoding="utf-8")
        print("  uv.lock", file=sys.stderr)

changelog = root / "CHANGELOG.md"
if changelog.is_file():
    ctext = changelog.read_text(encoding="utf-8")
    today = datetime.date.today().isoformat()
    ctext, n = re.subn(r"^## Unreleased[ \t]*$", f"## Unreleased\n\n## {new} — {today}", ctext, count=1, flags=re.M)
    if n:
        changelog.write_text(ctext, encoding="utf-8")
        print(f"  CHANGELOG.md: ## {new} — {today}", file=sys.stderr)
    else:
        print("  WARNING: CHANGELOG.md has no '## Unreleased' heading", file=sys.stderr)
print(new)
PY
)
"$PY" "$REPO_ROOT/scripts/build-catalog.py" --root "$PY_ROOT" >&2

echo "Release version: $NEW"
echo ""
echo "Next steps:"
echo "  Review the CHANGELOG.md section for $NEW, then open the release PR."
echo "  After it is merged: git tag v$NEW <merge commit> && git push origin v$NEW"
