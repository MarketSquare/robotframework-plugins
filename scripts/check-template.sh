#!/usr/bin/env bash
# Prove that the starter plugin passes every PR check (spec
# programme-documentation, "Template plugin passes CI"; launch task 9.4).
#
# Copies the tracked files of this checkout to a scratch folder, adds
# templates/plugin/ as plugins/example/ with its CODEOWNERS line, regenerates
# the catalogue, and runs the PR checks and tests there.
# Usage: scripts/check-template.sh [SCRATCH_DIR]
set -euo pipefail

root=$(git rev-parse --show-toplevel)
scratch=$(realpath -m "${1:-$(mktemp -d)}")
mkdir -p "$scratch"
git -C "$root" ls-files -z | (cd "$root" && xargs -0 cp -P --parents -t "$scratch")
cd "$scratch"
git init -q && git add -A && git -c user.name=check -c user.email=check@example.invalid commit -qm base
cp -r templates/plugin plugins/example
echo "/plugins/example/ @your-github-handle" >> .github/CODEOWNERS

python scripts/build-catalog.py
python scripts/build-catalog.py --check
python scripts/check-governance.py
python scripts/check_content_rules.py
python scripts/validate-skills.py --channel all
python scripts/check-plugin-references.py
bash scripts/check-drift.sh
python scripts/check-docs-voice.py
python -m pytest -q -p no:cacheprovider tests/ --ignore=tests/eval
# The plugin tests CI would select for a PR that adds plugins/example/.
printf 'plugins/example/catalog.yaml\n' > "$scratch/changed.txt"
for plugin in $(python scripts/select-plugin-tests.py --paths-file "$scratch/changed.txt"); do
  python -m pytest -q -p no:cacheprovider "plugins/$plugin/tests"
done
echo "template plugin passes the PR checks"
