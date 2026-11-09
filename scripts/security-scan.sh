#!/usr/bin/env bash
# Scan one plugin's shipped content with the gate's scanners and compare the
# findings with its baseline (spec content-security-scanning; design D6, D8).
#
# Usage: scripts/security-scan.sh <plugin> <outdir> [--draft] [--deep]
#
# Scans only what the plugin ships: its tracked files without the top-level
# tests/ and evals/ (as the installer build does), copied to <outdir>/tree.
# A bundle (catalog.yaml with a bundle: list) ships its generated copy in
# bundles/<name>/; its findings are judged by its member plugins' baselines,
# mapped onto the copy (design D15), plus its own baseline if it has one.
# Cisco runs on skills/, on agents/ (lenient) and on the whole tree (lenient).
# Writes one SARIF file per scanner run, <outdir>/summary.md, and with --draft
# <outdir>/draft.yaml (baseline entries for the new findings, to review).
# Exits 1 when the comparison fails. Scanners come from SCANNERS (default
# .scanners/bin, see scripts/install-scanners.sh). Nothing in the plugin runs.
#
# SCAN_ROOT scans another checkout (the deep scan's PR tree): its plugins and
# baselines are read as data, while this script, compare-findings.py and the
# cc-audit configuration come from the checkout this script is in.
# --deep turns on the model passes (SkillSpector without --no-llm, Cisco
# --use-llm); they read ANTHROPIC_API_KEY and SECURITY_SCAN_MODEL.
set -euo pipefail

plugin=${1:?plugin name}
out=${2:?output directory}
shift 2
draft="" deep=""
for opt in "$@"; do
  case "$opt" in
    --draft) draft=1 ;;
    --deep) deep=1 ;;
    *) echo "security-scan: unknown option $opt" >&2; exit 2 ;;
  esac
done
here=$(cd "$(dirname "$0")/.." && pwd)
root=$(realpath "${SCAN_ROOT:-$(git rev-parse --show-toplevel)}")
bin=${SCANNERS:-$here/.scanners/bin}
case "$plugin" in */*|.*) echo "security-scan: bad plugin name $plugin" >&2; exit 2 ;; esac
[ -d "$root/plugins/$plugin" ] || { echo "security-scan: no plugins/$plugin" >&2; exit 2; }
members=$(python3 -c 'import sys, yaml; print(" ".join((yaml.safe_load(open(sys.argv[1])) or {}).get("bundle") or []))' \
  "$root/plugins/$plugin/catalog.yaml")
src="plugins/$plugin"
for member in $members; do
  case "$member" in */*|.*|"") echo "security-scan: bad bundle member '$member'" >&2; exit 2 ;; esac
done
[ -n "$members" ] && src="bundles/$plugin"

mkdir -p "$out"
out=$(realpath "$out")
tree="$out/tree/$src"
rm -rf "${out:?}/tree"
mkdir -p "$tree"
# Tracked, shipped files only: no tests/, evals/, caches or untracked files.
git -C "$root" ls-files -z -- "$src" \
  | grep -zv -E "^$src/(tests|evals)/" \
  | (cd "$root" && xargs -0 cp -P --parents -t "$out/tree")  # -P: copy a symlink as a link, never its target

model=${SECURITY_SCAN_MODEL:-claude-sonnet-5-5}
cisco_llm=() spector_llm=(--no-llm)
if [ -n "$deep" ]; then
  : "${ANTHROPIC_API_KEY:?--deep needs ANTHROPIC_API_KEY}"
  cisco_llm=(--use-llm --llm-provider anthropic)
  spector_llm=()
  export SKILL_SCANNER_LLM_MODEL="$model" SKILLSPECTOR_PROVIDER=anthropic SKILLSPECTOR_MODEL="$model"
fi

sarif=()
run() {  # run <name> <base> <command...>: scanner output to <out>/<name>.sarif
  local name=$1 base=$2; shift 2
  "$@" > "$out/$name.log" 2>&1 || true
  [ -s "$out/$name.sarif" ] || echo '{"version": "2.1.0", "runs": []}' > "$out/$name.sarif"
  sarif+=(--sarif "${name%%-*}=$out/$name.sarif${base:+@$base}")
}

cd "$out/tree"
if [ -d "$src/skills" ]; then
  run cisco-skills "" "$bin/skill-scanner" scan-all "$src/skills" --recursive "${cisco_llm[@]}" \
    --format sarif --output-sarif "$out/cisco-skills.sarif"
fi
if [ -d "$src/agents" ]; then
  run cisco-agents "" "$bin/skill-scanner" scan-all "$src/agents" --recursive --lenient "${cisco_llm[@]}" \
    --format sarif --output-sarif "$out/cisco-agents.sarif"
fi
# The whole shipped tree in lenient mode: the only Cisco pass that reads hooks
# and scripts (catches a hook that sends the environment out, canary C4).
run cisco-tree "" "$bin/skill-scanner" scan "$src" --lenient "${cisco_llm[@]}" \
  --format sarif --output-sarif "$out/cisco-tree.sarif"
run skillspector "$src" "$bin/skillspector" scan "$src" --recursive "${spector_llm[@]}" \
  --format sarif --output "$out/skillspector.sarif"
for type in mcp plugin hook subagent; do
  "$bin/cc-audit" check --config "$here/security/cc-audit.yaml" -t "$type" --format sarif "$src" \
    > "$out/cc-audit-$type.sarif" 2> "$out/cc-audit-$type.log" || true
  [ -s "$out/cc-audit-$type.sarif" ] || echo '{"version": "2.1.0", "runs": []}' > "$out/cc-audit-$type.sarif"
  sarif+=(--sarif "cc-audit=$out/cc-audit-$type.sarif")
done
run gitleaks "" "$bin/gitleaks" dir "$src" --no-banner --redact --exit-code 0 \
  --report-format sarif --report-path "$out/gitleaks.sarif"
cd "$root"

args=(--baseline "$root/security/baselines/$plugin.yaml" --plugin "$plugin" --summary "$out/summary.md" "${sarif[@]}")
for member in $members; do
  args+=(--baseline "$root/security/baselines/$member.yaml" --map "plugins/$member/=$src/")
done
[ -n "$draft" ] && args+=(--draft "$out/draft.yaml")
python3 "$here/scripts/compare-findings.py" "${args[@]}"
