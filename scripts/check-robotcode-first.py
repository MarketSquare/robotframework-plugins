#!/usr/bin/env python3
"""Fail when repository tooling re-implements what the robotcode CLI does.

Spec robotcode-first-tooling, "Automated guard with a reasoned allowlist".
Scans the tooling paths for direct uses of Robot Framework APIs and commands
that RobotCode covers (libdoc, result parsing, suite building, the parser
model, starting robot/rebot/libdoc). Each use needs an entry in
scripts/robotcode-first-allowlist.toml that names the file, the pattern and
why RobotCode doesn't cover it; an entry that matches nothing fails.

It matches imports and calls, not prose, and skips comment lines. It is a
tripwire for honest contributors and agents, not a sandbox.

Usage: python scripts/check-robotcode-first.py [--root DIR] [--allowlist FILE]
Exit codes: 0 clean, 1 findings or stale entries, 2 usage error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALLOWLIST = REPO_ROOT / "scripts" / "robotcode-first-allowlist.toml"

# Tooling paths, relative to the root. Globs expand to directories.
TOOLING_GLOBS = ("scripts", "src", "plugins/*/scripts", "plugins/*/skills/*/scripts", "plugins/*/hooks")
SUFFIXES = {".py", ".mjs", ".js"}

_NAMES = r"(?:robot|rebot|libdoc)"
PATTERNS: dict[str, re.Pattern[str]] = {
    "libdoc": re.compile(r"\brobot\.libdoc(?:pkg)?\b|\bLibraryDocumentation\b"),
    "execution-result": re.compile(r"\bExecutionResult\b"),
    "xml-parsing": re.compile(r"\bxml\.etree\b|\bElementTree\b"),
    "suite-builder": re.compile(r"\bTestSuiteBuilder\b"),
    "parser-model": re.compile(r"\bget_(?:resource_|init_)?model\s*\(|\bModelVisitor\b"),
    # Starting robot, rebot or libdoc (Python): the first argv element, the
    # tool after `uvx --from <spec>`, `-m robot`, a lookup of the executable,
    # or a path built to it. `[robotcode, "robot", ...]` is the subcommand.
    "run-robot": re.compile(
        rf"\[\s*[\"']{_NAMES}[\"']\s*[,\]]"
        rf"|[\"']--from[\"']\s*,\s*[^,\]]+,\s*[\"']{_NAMES}[\"']"
        rf"|[\"']-m[\"']\s*,\s*[\"']robot(?:\.libdoc|\.rebot)?[\"']"
        rf"|\b(?:which|_which|_tool)\(\s*[\"']{_NAMES}[\"']\s*\)"
        rf"|/\s*[\"']{_NAMES}[\"']"
    ),
}

# JavaScript passes the command separately (`spawnSync(cmd, [args])`), so an
# argument list that starts with "robot" is a subcommand, as in robotcode's.
JS_PATTERNS = dict(PATTERNS)
JS_PATTERNS["run-robot"] = re.compile(
    rf"\b(?:spawn|spawnSync|execFile|execFileSync)\(\s*[\"']{_NAMES}[\"']"
    rf"|[\"']-m[\"']\s*,\s*[\"']robot(?:\.libdoc|\.rebot)?[\"']"
)

_COMMENT = re.compile(r"^\s*(?:#|//|/\*|\*)")


def tooling_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in TOOLING_GLOBS:
        for base in root.glob(pattern):
            if base.is_dir():
                files.update(p for p in base.rglob("*") if p.is_file() and p.suffix in SUFFIXES)
    this = Path(__file__).resolve()
    return sorted(f for f in files
                  if "__pycache__" not in f.parts and "node_modules" not in f.parts and f.resolve() != this)


def find_uses(root: Path) -> list[tuple[str, int, str]]:
    """(relative file, line number, pattern name) for every use."""
    uses = []
    for path in tooling_files(root):
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        patterns = PATTERNS if path.suffix == ".py" else JS_PATTERNS
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _COMMENT.match(line):
                continue
            for name, rx in patterns.items():
                if rx.search(line):
                    uses.append((rel, lineno, name))
    return uses


def load_allowlist(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    if tomllib is None:
        raise SystemExit("ERROR: reading the allowlist needs Python 3.11+ (tomllib)")
    entries = tomllib.loads(path.read_text(encoding="utf-8")).get("allow", [])
    for i, entry in enumerate(entries, start=1):
        missing = [k for k in ("file", "pattern", "reason") if not str(entry.get(k, "")).strip()]
        if missing:
            raise SystemExit(f"ERROR: allowlist entry {i} lacks {', '.join(missing)}")
        if entry["pattern"] not in PATTERNS:
            raise SystemExit(f"ERROR: allowlist entry {i} has unknown pattern {entry['pattern']!r} "
                             f"(known: {', '.join(PATTERNS)})")
    return entries


def check(root: Path, allowlist: Path) -> int:
    entries = load_allowlist(allowlist)
    allowed = {(e["file"], e["pattern"]) for e in entries}
    uses = find_uses(root)
    used = {(f, p) for f, _, p in uses}

    findings = [(f, n, p) for f, n, p in uses if (f, p) not in allowed]
    stale = [e for e in entries if (e["file"], e["pattern"]) not in used]

    for f, n, p in findings:
        print(f"{f}:{n}: {p}: use the robotcode CLI instead, or add an allowlist entry with the reason")
    for e in stale:
        print(f"stale allowlist entry: {e['file']} ({e['pattern']}) matches nothing; remove it")
    if findings or stale:
        print(f"robotcode first: {len(findings)} finding(s), {len(stale)} stale entr{'y' if len(stale) == 1 else 'ies'}")
        return 1
    print(f"robotcode first: OK ({len(uses)} allowlisted use(s) in {len({f for f, _ in used})} file(s))")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=str(REPO_ROOT), help="repository root to scan")
    parser.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST), help="allowlist TOML")
    args = parser.parse_args(argv)
    return check(Path(args.root), Path(args.allowlist))


if __name__ == "__main__":
    sys.exit(main())
