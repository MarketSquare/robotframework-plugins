#!/usr/bin/env python3
"""Docs voice check (spec programme-documentation, "Documents follow the
Robot Framework Voice"; design D10).

Checks the mechanical part of the voice guide in documents written for
people: no banned corporate phrase, and at most one exclamation mark per
document. Code (fenced blocks and inline code), link targets and HTML
comments are not prose and are skipped. Everything else in the guide is a
review checklist item.

Documents: the top-level *.md files, docs/ (without generated reports),
installer/README.md, every plugin's and template's README.md, and the
template's other Markdown. Changelogs and dated records (a ``**Date:**``
line near the top: reports, test results, plans) are history and are skipped.

Usage: scripts/check-docs-voice.py [--root DIR] [FILE ...]
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Phrase -> pattern. The first five are the spec's list; the rest are the same
#: kind of filler. Matching ignores case.
BANNED = {
    "Our mission is": r"\bour mission is\b",
    "leverage": r"\bleverag(?:e|es|ed|ing)\b",
    "best-in-class": r"\bbest[- ]in[- ]class\b",
    "seamless": r"\bseamless(?:ly)?\b",
    "world-class": r"\bworld[- ]class\b",
    "cutting-edge": r"\bcutting[- ]edge\b",
    "game-changer": r"\bgame[- ]chang(?:er|ing)\b",
    "revolutionize": r"\brevolutioni[sz](?:e|es|ed|ing)\b",
    "next-generation": r"\bnext[- ]generation\b",
    "synergy": r"\bsynerg(?:y|ies|istic)\b",
    "unlock the power": r"\bunlock(?:s|ing)? the (?:full )?power\b",
    "supercharge": r"\bsupercharg(?:e|es|ed|ing)\b",
}
BANNED_RE = {phrase: re.compile(rx, re.IGNORECASE) for phrase, rx in BANNED.items()}
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`+[^`]*`+")
LINK_TARGET = re.compile(r"\]\([^)]*\)")
HTML_COMMENT = re.compile(r"<!--.*?-->")
#: "!" that isn't an exclamation: images, "!=", shell history, the `!` prefix.
NOT_EXCLAMATION = re.compile(r"!\[|!=")


DATED = re.compile(r"^\*\*Date:\*\*", re.MULTILINE)


def is_dated_record(path: Path) -> bool:
    head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:12])
    return bool(DATED.search(head))


def documents(root: Path) -> list[Path]:
    found: set[Path] = set(root.glob("*.md"))
    found |= {p for p in (root / "docs").rglob("*.md") if "reports" not in p.relative_to(root / "docs").parts}
    found |= {root / "installer" / "README.md"}
    found |= set(root.glob("plugins/*/README.md"))
    found |= set((root / "templates").rglob("*.md")) if (root / "templates").is_dir() else set()
    return sorted(p for p in found if p.is_file() and "CHANGELOG" not in p.name and not is_dated_record(p))


def prose_lines(text: str) -> Iterator[tuple[int, str]]:
    """``(line number, prose)``: code, link targets and comments removed."""
    fenced = False
    text = HTML_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    for no, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        yield no, LINK_TARGET.sub("]", INLINE_CODE.sub("", line))


def check(path: Path, root: Path) -> list[str]:
    rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
    problems = []
    marks: list[int] = []
    for no, line in prose_lines(path.read_text(encoding="utf-8")):
        for phrase, rx in BANNED_RE.items():
            if rx.search(line):
                problems.append(f"{rel}:{no}: banned phrase \"{phrase}\"")
        marks += [no] * NOT_EXCLAMATION.sub("", line).count("!")
    if len(marks) > 1:
        lines = ", ".join(map(str, marks))
        problems.append(f"{rel}: {len(marks)} exclamation marks (lines {lines}); at most one per document")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("files", nargs="*", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    files = [f.resolve() for f in args.files] or documents(root)
    problems = [p for f in files for p in check(f, root)]
    for p in problems:
        print(p)
    if not problems:
        print(f"docs voice: {len(files)} document(s) OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
