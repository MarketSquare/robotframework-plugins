#!/usr/bin/env bash
# Usage: ./scripts/bump-version.sh <plugin> <major|minor|patch>
# Bumps one plugin's version (see RELEASING.md) everywhere it is recorded:
#   plugins/<plugin>/.claude-plugin/plugin.json (the one source of truth) and
#   metadata.version in every plugins/<plugin>/skills/*/SKILL.md (checked by
#   validate-skills.py). Then regenerate the marketplace and catalogue with
#   scripts/build-catalog.py. Marketplace entries carry no version.
#
# REPO_ROOT can be overridden (used by tests to run against a scratch tree).
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
# Python and a root path it can open: on Windows (Git Bash) python3 may not
# exist and /d/a/... paths are not valid for a native Windows Python.
PY="$(command -v python3 || command -v python)"
if command -v cygpath >/dev/null 2>&1; then PY_ROOT="$(cygpath -m "$REPO_ROOT")"; else PY_ROOT="$REPO_ROOT"; fi

if [ $# -ne 2 ]; then
    echo "Usage: $0 <plugin> <major|minor|patch>" >&2
    exit 1
fi
PLUGIN="$1"
BUMP_TYPE="$2"
case "$BUMP_TYPE" in
    major|minor|patch) ;;
    *) echo "Usage: $0 <plugin> <major|minor|patch>" >&2; exit 1 ;;
esac
if [ ! -f "$REPO_ROOT/plugins/$PLUGIN/.claude-plugin/plugin.json" ]; then
    echo "ERROR: plugins/$PLUGIN/.claude-plugin/plugin.json not found" >&2
    exit 1
fi

"$PY" - "$PY_ROOT" "$PLUGIN" "$BUMP_TYPE" <<'PY'
import json
import re
import sys
from pathlib import Path

root, plugin, bump = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
manifest = root / "plugins" / plugin / ".claude-plugin" / "plugin.json"
data = json.loads(manifest.read_text(encoding="utf-8"))
current = data.get("version")
if not current:
    sys.exit(f"ERROR: {manifest.relative_to(root)} has no version")
major, minor, patch = (int(p) for p in current.split("."))
if bump == "major":
    major, minor, patch = major + 1, 0, 0
elif bump == "minor":
    minor, patch = minor + 1, 0
else:
    patch += 1
new = f"{major}.{minor}.{patch}"
data["version"] = new
manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"  {manifest.relative_to(root).as_posix()}")

# metadata.version in each SKILL.md frontmatter (the indented `version:`
# line of the metadata map, inside the leading --- block only).
skill_globs = [f"plugins/{plugin}/skills/*/SKILL.md"]
pattern = re.compile(r"^(metadata:[ \t]*\n(?:[ \t]+[^\n]*\n)*?[ \t]+version:[ \t]*)[^\n]*$", re.M)
for glob in skill_globs:
    for skill_md in sorted(root.glob(glob)):
        text = skill_md.read_text(encoding="utf-8")
        end = text.find("\n---", 3) if text.startswith("---\n") else -1
        new_fm, n = pattern.subn(lambda m: f'{m.group(1)}"{new}"', text[:end + 1], count=1) if end > 0 else ("", 0)
        if n:
            skill_md.write_text(new_fm + text[end + 1:], encoding="utf-8")
            print(f"  {skill_md.relative_to(root).as_posix()}")
        else:
            print(f"  WARNING: no metadata.version in {skill_md.relative_to(root).as_posix()}", file=sys.stderr)
print(f"Bumped {plugin}: {current} -> {new}")
print("")
print("Next steps:")
print("  python3 scripts/build-catalog.py && python3 scripts/validate-skills.py --channel all")
print(f"  git add -A && git commit -m 'release: {plugin} {new}'")
print(f"  git tag {plugin}--v{new} && git push origin main {plugin}--v{new}")
PY
