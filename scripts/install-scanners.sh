#!/usr/bin/env bash
# Install the security gate's scanners at pinned versions, each isolated
# (spec content-security-scanning, "Static scanners gate every PR without
# secrets"; design D6).
#
#   Cisco skill-scanner 2.3.2   PyPI, own virtualenv
#   SkillSpector 2.13.4         git tag v2.13.4 pinned to its commit, own virtualenv
#   cc-audit 3.23.37            GitHub release binary, SHA-256 checked
#                               (the npm package of that name links to no repository)
#   Gitleaks 8.30.1             GitHub release binary, SHA-256 checked
#
# Usage: scripts/install-scanners.sh [DIR]   (default: .scanners)
# Puts a launcher for every tool in DIR/bin and prints each tool's version.
# Needs uv, git, curl, tar and sha256sum. Linux x86_64 or aarch64.
set -euo pipefail

DIR=$(realpath -m "${1:-.scanners}")
BIN="$DIR/bin"
PYTHON=3.12

CISCO_VERSION=2.3.2
SKILLSPECTOR_VERSION=2.13.4
SKILLSPECTOR_COMMIT=54824463814a0be01360792523ec7245a69190fc
CC_AUDIT_VERSION=3.23.37
GITLEAKS_VERSION=8.30.1

case "$(uname -m)" in
  x86_64)
    CC_AUDIT_TARGET=x86_64-unknown-linux-gnu
    CC_AUDIT_SHA256=b5a3b70aff66f8a50aebefd39d86c8a3e3bcb785de0aaacb30c2aef8897928d5
    GITLEAKS_ARCH=x64
    GITLEAKS_SHA256=551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb
    ;;
  aarch64)
    CC_AUDIT_TARGET=aarch64-unknown-linux-gnu
    CC_AUDIT_SHA256=251b38085be4a9b6b217387c8c84eeeffd461c7386112dc455f6d334c8f4f25f
    GITLEAKS_ARCH=arm64
    GITLEAKS_SHA256=e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080
    ;;
  *) echo "install-scanners: unsupported machine $(uname -m)" >&2; exit 2 ;;
esac

for tool in uv git curl tar sha256sum; do
  command -v "$tool" >/dev/null || { echo "install-scanners: $tool is required" >&2; exit 2; }
done
mkdir -p "$BIN"

# A Python tool in its own virtualenv; DIR/bin/<command> runs it.
python_tool() {
  local name=$1 spec=$2; shift 2
  uv venv --quiet --python "$PYTHON" "$DIR/$name"
  VIRTUAL_ENV="$DIR/$name" uv pip install --quiet "$spec"
  for cmd in "$@"; do ln -sf "$DIR/$name/bin/$cmd" "$BIN/$cmd"; done
}

# A release tarball whose SHA-256 must match; extracts <binary> into DIR/<name>.
release_binary() {
  local name=$1 url=$2 sha=$3 binary=$4
  local tmp
  tmp=$(mktemp -d)
  curl --fail --silent --show-error --location --proto '=https' --output "$tmp/archive.tar.gz" "$url"
  echo "$sha  $tmp/archive.tar.gz" | sha256sum --check --quiet --strict
  mkdir -p "$DIR/$name"
  tar -xzf "$tmp/archive.tar.gz" -C "$DIR/$name" --no-same-owner
  local found
  found=$(find "$DIR/$name" -type f -name "$binary" | head -1)
  [ -n "$found" ] || { echo "install-scanners: $binary not in $url" >&2; exit 1; }
  chmod 0755 "$found"
  ln -sf "$found" "$BIN/$binary"
  rm -rf "$tmp"
}

python_tool cisco "cisco-ai-skill-scanner==$CISCO_VERSION" skill-scanner
python_tool skillspector "skillspector @ git+https://github.com/NVIDIA/skillspector@$SKILLSPECTOR_COMMIT" skillspector
release_binary cc-audit \
  "https://github.com/ryo-ebata/cc-audit/releases/download/v$CC_AUDIT_VERSION/cc-audit-v$CC_AUDIT_VERSION-$CC_AUDIT_TARGET.tar.gz" \
  "$CC_AUDIT_SHA256" cc-audit
release_binary gitleaks \
  "https://github.com/gitleaks/gitleaks/releases/download/v$GITLEAKS_VERSION/gitleaks_${GITLEAKS_VERSION}_linux_$GITLEAKS_ARCH.tar.gz" \
  "$GITLEAKS_SHA256" gitleaks

# Each tool must report the version pinned above.
check_version() {
  local label=$1 want=$2; shift 2
  local out
  out=$("$@" 2>&1 | tail -n 3 | tr '\n' ' ')
  case "$out" in
    *"$want"*) printf '%-14s %s\n' "$label" "$want" ;;
    *) echo "install-scanners: $label reports '$out', expected $want" >&2; exit 1 ;;
  esac
}
check_version skill-scanner "$CISCO_VERSION" "$BIN/skill-scanner" --version
check_version skillspector "$SKILLSPECTOR_VERSION" "$BIN/skillspector" --version
check_version cc-audit "$CC_AUDIT_VERSION" "$BIN/cc-audit" --version
check_version gitleaks "$GITLEAKS_VERSION" "$BIN/gitleaks" version
echo "scanners in $BIN"
