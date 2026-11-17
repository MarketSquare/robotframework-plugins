#!/usr/bin/env python3
"""Check that library skills only teach keywords that exist and are not deprecated.

Repository QA tooling (not shipped with the skills); spec
skill-content-verification, design D1 of robotcode-first-tooling. For every
library skill under ``--skills-root`` it:

1. writes the skill's Robot Framework content into a temporary project: one
   ``.robot`` file per fenced ```robotframework / ```robot block (a fragment
   without section headers becomes the body of a generated test), copies of
   its ``.robot`` / ``.resource`` files, and one ``skill.resource`` with every
   ``*** Keywords ***`` section, imported everywhere, so a keyword defined in
   one block resolves in another. Every file imports the skill's target
   library and the standard libraries;
2. runs ``robotcode analyze code`` on that project and maps each diagnostic
   back to the Markdown or example file and line it came from;
3. reports ``UNKNOWN`` (``KeywordNotFound``, with close matches from
   ``robotcode doc keywords``), ``DEPRECATED`` (``DeprecatedKeyword``),
   ``ARGS`` (argument errors), ``LEGACY`` (Robocop ``DEPR08``: ``Run Keyword
   If`` / ``Unless``) and ``BAD-ARG`` (Browser ``Wait For Condition`` with a
   condition name that is not a ``ConditionInputs`` member; RobotCode doesn't
   check enum arguments).

Intentional exceptions live in ``scripts/skill-keywords-allowlist.toml``::

    [[allow]]
    skill = "browser"                    # short skill key
    file = "references/locators.md"      # path relative to the skill dir
    keyword = "Create New Item"
    reason = "illustrative application keyword"

An allowlist entry that matches nothing fails the run (stale entry).

Needs ``robotcode`` and ``robocop`` (``robotcode[all]``) and the target
libraries installed. Exit status: 0 clean, 1 findings / stale entries /
skipped skills with ``--require-all``, 2 usage error.
"""

from __future__ import annotations

import argparse
import difflib
import functools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover - Python < 3.11
    tomllib = None

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ALLOWLIST = REPO_ROOT / "scripts" / "skill-keywords-allowlist.toml"

# Skill key (dir name without the "rf-" prefix) -> libdoc import name.
SKILL_LIBRARIES = {
    "browser": "Browser",
    "selenium": "SeleniumLibrary",
    "appium": "AppiumLibrary",
    "requests": "RequestsLibrary",
    "restinstance": "REST",
    "platynui": "PlatynUI.BareMetal",
}
STANDARD_LIBRARIES = [
    "BuiltIn",
    "Collections",
    "String",
    "OperatingSystem",
    "DateTime",
    "Process",
    "XML",
    "Screenshot",
]
# Prefixes that may qualify a keyword call (``Browser.Click``).
LIBRARY_PREFIXES = {
    "browser", "seleniumlibrary", "appiumlibrary", "requestslibrary", "rest",
    "platynui.baremetal", "baremetal", *(lib.lower() for lib in STANDARD_LIBRARIES),
}

CONTROL = {
    "IF", "ELSE", "ELSE IF", "END", "FOR", "WHILE", "TRY", "EXCEPT", "FINALLY",
    "RETURN", "BREAK", "CONTINUE", "VAR", "GROUP",
}
SETUP_SETTINGS = {
    "suite setup", "suite teardown", "test setup", "test teardown",
    "task setup", "task teardown", "test template", "task template",
}
OTHER_SETTINGS = {
    "library", "resource", "variables", "documentation", "metadata", "name",
    "force tags", "default tags", "test tags", "task tags", "keyword tags",
    "test timeout", "task timeout",
}
LEGACY = {"runkeywordif", "runkeywordunless"}

FENCE_OPEN = re.compile(r"^(?P<indent>[ \t]*)```\s*(?:robotframework|robot)\s*$", re.I)
FENCE_CLOSE = re.compile(r"^[ \t]*```\s*$")
SECTION = re.compile(r"^\*{3}\s*(.*?)\s*\*{3}")
CELL_SPLIT = re.compile(r"\s{2,}|\t|\s\|\s")


def normalize(name: str) -> str:
    return re.sub(r"[\s_]+", "", name).lower()


def is_variable(cell: str) -> bool:
    return bool(re.match(r"^[$@&%]\{", cell))


def looks_like_keyword(name: str) -> bool:
    return bool(re.match(r"^[A-Za-z]", name)) and not re.search(r"[/<>\"'()]|\.\.\.|…", name)


@dataclass
class Finding:
    skill: str
    file: str
    line: int
    kind: str
    keyword: str
    detail: str = ""

    def format(self) -> str:
        text = f"{self.skill} {self.file}:{self.line} {self.kind} {self.keyword}"
        return f"{text} ~ {self.detail}" if self.detail else text


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------


def split_cells(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("| "):
        s = s.strip("|").strip()
    cells = []
    for cell in CELL_SPLIT.split(s):
        cell = cell.strip()
        if not cell:
            continue
        if cell.startswith("#"):
            break
        cells.append(re.sub(r"\s+#.*$", "", cell))
    return cells


# --------------------------------------------------------------------------
# Resolution
# --------------------------------------------------------------------------


def strip_prefix(name: str) -> str:
    if "." in name:
        prefix, _, rest = name.rpartition(".")
        if prefix.lower() in LIBRARY_PREFIXES and rest:
            return rest
    return name


# --------------------------------------------------------------------------
# Materialise the snippets, let RobotCode resolve (design D1)
# --------------------------------------------------------------------------

# A line of a generated file and where it came from (skill-relative file, line).
Origin = tuple[str, int] | None
_ARG_ERROR = re.compile(r"argument", re.I)
_QUOTED = re.compile(r"'([^']+)'")
# Robocop's simple output with a fixed issue format, as the rf-core hooks use (Robocop 8 and 9).
ROBOCOP_FORMAT = ["-c", "print_issues.output_format=simple", "--issue-format", "{rule_id}|{line}|{source}"]
_ROBOCOP_LINE = re.compile(r"^(?P<rule>DEPR08)\|(?P<line>\d+)\|(?P<path>.+)$")


@dataclass
class Generated:
    lines: list[tuple[str, Origin]] = field(default_factory=list)

    def add(self, text: str, origin: Origin = None) -> None:
        self.lines.append((text, origin))

    def write(self, path: Path) -> list[Origin]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(t for t, _ in self.lines) + "\n", encoding="utf-8")
        return [o for _, o in self.lines]


def _robotcode() -> str:
    exe = Path(sys.executable).parent / "robotcode"
    return str(exe) if exe.is_file() else (shutil.which("robotcode") or "robotcode")


def _robotcode_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """UTF-8 output, so library docs with non-ASCII text don't crash robotcode on a Windows code page."""
    return {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", **(extra or {})}


@functools.lru_cache(maxsize=None)
def robotcode_keywords(library: str) -> dict[str, str] | None:
    """Keyword name -> short doc of ``library`` from ``robotcode doc keywords``; None when it doesn't load."""
    proc = subprocess.run([_robotcode(), "--format", "json", "doc", "keywords", library],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
                          timeout=300, env=_robotcode_env())
    try:
        return {str(k["name"]): str(k.get("short_doc") or "") for k in json.loads(proc.stdout).get("keywords", [])}
    except (json.JSONDecodeError, AttributeError):
        return None


def _imports(library: str, resource: str | None) -> list[str]:
    lines = ["*** Settings ***", f"Library    {library}"]
    lines += [f"Library    {std}" for std in STANDARD_LIBRARIES if std != "BuiltIn"]
    if resource:
        lines.append(f"Resource    {resource}")
    return lines


def _split_sections(lines: list[str], start: int, rel: str) -> list[tuple[str | None, list[tuple[str, Origin]]]]:
    """(section name or None, its lines with origins), in order."""
    out: list[tuple[str | None, list[tuple[str, Origin]]]] = [(None, [])]
    for i, raw in enumerate(lines):
        m = SECTION.match(raw)
        if m:
            out.append((m.group(1).lower().rstrip("s"), [(raw, (rel, start + i))]))
        else:
            out[-1][1].append((raw, (rel, start + i)))
    return out


def _fragment(lines: list[str], start: int, rel: str, n: int, gen: Generated) -> None:
    """A block without section headers: settings rows, then a test body."""
    settings: list[tuple[str, Origin]] = []
    body: list[tuple[str, Origin]] = []
    for i, raw in enumerate(lines):
        cells = split_cells(raw)
        target = body
        if cells and not raw[:1].isspace() and cells[0].lower() in SETUP_SETTINGS | OTHER_SETTINGS:
            target = settings
        elif raw.strip().startswith("...") and body == [] and settings:
            target = settings
        target.append((raw, (rel, start + i)))
    for text, origin in settings:
        gen.add(text, origin)
    if not any(t.strip() and not t.strip().startswith("#") for t, _ in body):
        return
    named = False
    for idx, (text, _) in enumerate(body):
        cells = split_cells(text)
        if not text[:1].isspace() and len(cells) == 1 and cells[0].upper() not in CONTROL:
            nxt = next((t for t, _ in body[idx + 1:] if t.strip() and not t.strip().startswith("#")), "")
            if nxt[:1].isspace():
                named = True
                break
    gen.add("*** Test Cases ***")
    if named:
        for text, origin in body:
            gen.add(text, origin)
    else:
        gen.add(f"Snippet {n}")
        for text, origin in body:
            gen.add(f"    {text}" if text.strip() else "", origin)


def materialise(skill_dir: Path, library: str, out: Path) -> tuple[dict[str, list[Origin]], int]:
    """Write the skill's Robot Framework content as a project under ``out``.

    Returns the line table (generated file -> origin per line) and the number
    of source files read.
    """
    tables: dict[str, list[Origin]] = {}
    keywords = Generated()  # every *** Keywords *** section of the skill
    resources: list[str] = []
    files = sorted(p for p in skill_dir.rglob("*") if p.is_file() and p.suffix in (".md", ".robot", ".resource"))
    n = 0
    for path in files:
        rel = path.relative_to(skill_dir).as_posix()
        if path.suffix == ".md":
            lines = path.read_text(encoding="utf-8").splitlines()
            i = 0
            while i < len(lines):
                if not FENCE_OPEN.match(lines[i]):
                    i += 1
                    continue
                start = i + 1
                j = start
                while j < len(lines) and not FENCE_CLOSE.match(lines[j]):
                    j += 1
                block = textwrap.dedent("\n".join(lines[start:j])).splitlines()
                n += 1
                gen = Generated()
                for text in _imports(library, "skill.resource"):
                    gen.add(text)
                sections = _split_sections(block, start + 1, rel)
                if len(sections) == 1:
                    _fragment(block, start + 1, rel, n, gen)
                else:
                    for name, sec in sections:
                        target = keywords if name == "keyword" else gen
                        for text, origin in sec:
                            target.add(text, origin)
                tables[f"block_{n:03d}.robot"] = gen.write(out / f"block_{n:03d}.robot")
                i = j + 1
        else:
            dest = f"files/{rel}"
            to_root = os.path.relpath(out / "skill.resource", (out / dest).parent)
            gen = Generated()
            for text in _imports(library, None if path.suffix == ".resource" else Path(to_root).as_posix()):
                gen.add(text)
            raw = path.read_text(encoding="utf-8").splitlines()
            for name, sec in _split_sections(raw, 1, rel):
                for text, origin in sec:
                    gen.add(text, origin)
                if name == "keyword" and path.suffix == ".robot":
                    for text, origin in sec:
                        keywords.add(text, origin)
            tables[dest] = gen.write(out / dest)
            if path.suffix == ".resource":
                resources.append(dest)
    res = Generated()
    for text in _imports(library, None):
        res.add(text)
    for dest in resources:
        res.add(f"Resource    {dest}")
    res.lines += keywords.lines
    tables["skill.resource"] = res.write(out / "skill.resource")
    return tables, len(files)


def _origin(tables: dict[str, list[Origin]], root: Path, path: str, line: int) -> Origin:
    rel = Path(path)
    rel = rel.relative_to(root) if rel.is_absolute() else rel
    table = tables.get(rel.as_posix())
    if table is None or not 1 <= line <= len(table):
        return None
    return table[line - 1]


def _bare(name: str) -> str:
    return strip_prefix(name.split(".", 1)[1]) if "." in name and name.split(".", 1)[0] in (
        *SKILL_LIBRARIES.values(), *STANDARD_LIBRARIES) else strip_prefix(name)


def check_skill(skill: str, skill_dir: Path, library: str,
                          condition_inputs: dict[str, str] | None) -> tuple[list[Finding], int]:
    docs: dict[str, str] = {}
    for lib in (*STANDARD_LIBRARIES, library):
        docs.update(robotcode_keywords(lib) or {})
    by_norm = {normalize(n): n for n in sorted(docs)}
    short_docs = {normalize(n): d for n, d in docs.items()}

    def suggest(name: str) -> str:
        close = difflib.get_close_matches(normalize(name), list(by_norm), n=3, cutoff=0.6)
        return ", ".join(by_norm[c] for c in close)

    findings: list[Finding] = []
    with tempfile.TemporaryDirectory(prefix="skill-keywords-") as tmp:
        root = Path(tmp) / "project"
        tables, nfiles = materialise(skill_dir, library, root)
        env = _robotcode_env({"ROBOTCODE_CACHE_DIR": str(Path(tmp) / "cache")})
        proc = subprocess.run([_robotcode(), "--format", "json", "analyze", "code", "."],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
                              timeout=1800, cwd=root, env=env)
        data = json.loads(proc.stdout)
        for path, diags in (data.get("diagnostics") or {}).items():
            for d in diags:
                origin = _origin(tables, root, path, int(d["range"]["start"]["line"]) + 1)
                if origin is None:
                    continue
                code, message = str(d.get("code") or ""), str(d.get("message") or "").splitlines()[0]
                quoted = _QUOTED.search(message)
                keyword = _bare(quoted.group(1)) if quoted else ""
                if code == "KeywordNotFound":
                    if keyword and not is_variable(keyword) and looks_like_keyword(keyword):
                        findings.append(Finding(skill, origin[0], origin[1], "UNKNOWN", keyword, suggest(keyword)))
                elif code == "DeprecatedKeyword":
                    # RobotCode's message drops the reason (robotcode issue draft 3); the short doc keeps it.
                    detail = short_docs.get(normalize(keyword), "").replace("\n", " ") or message
                    findings.append(Finding(skill, origin[0], origin[1], "DEPRECATED", keyword, detail))
                elif code == "DataError" and _ARG_ERROR.search(message) and not message.startswith("Importing"):
                    findings.append(Finding(skill, origin[0], origin[1], "ARGS", keyword, message))
        robocop = subprocess.run([shutil.which("robocop") or "robocop", "check", "--no-cache", *ROBOCOP_FORMAT,
                                  "--select", "DEPR08", "."],
                                 capture_output=True, text=True, check=False, timeout=600, cwd=root)
        for line in robocop.stdout.splitlines():
            m = _ROBOCOP_LINE.match(line.strip())
            if m:
                origin = _origin(tables, root, m.group("path"), int(m.group("line")))
                if origin:
                    cells = split_cells(_line_at(root, m.group("path"), int(m.group("line"))))
                    kw = next((c for c in cells if normalize(c) in LEGACY), "Run Keyword If")
                    findings.append(Finding(skill, origin[0], origin[1], "LEGACY", kw, "use native IF / ELSE"))
        if condition_inputs:
            findings += _wait_for_condition(skill, root, tables, condition_inputs)
    unique = {(f.file, f.line, f.kind, normalize(f.keyword)): f for f in findings}
    return list(unique.values()), nfiles


def _line_at(root: Path, path: str, line: int) -> str:
    p = Path(path) if Path(path).is_absolute() else root / path
    lines = p.read_text(encoding="utf-8").splitlines()
    return lines[line - 1] if 1 <= line <= len(lines) else ""


def _wait_for_condition(skill: str, root: Path, tables: dict[str, list[Origin]],
                        condition_inputs: dict[str, str]) -> list[Finding]:
    out = []
    for rel, table in tables.items():
        lines = (root / rel).read_text(encoding="utf-8").splitlines()
        for i, text in enumerate(lines):
            cells = split_cells(text)
            for k, cell in enumerate(cells[:-1]):
                if normalize(strip_prefix(cell)) != "waitforcondition":
                    continue
                cond = cells[k + 1]
                value = cond.split("=", 1)[1] if cond.lower().startswith("condition=") else cond
                if not is_variable(value) and normalize(value) not in condition_inputs and table[i]:
                    out.append(Finding(skill, table[i][0], table[i][1], "BAD-ARG", f"{cell}    {cond}",
                                       "condition must be one of: " + ", ".join(sorted(condition_inputs.values()))))
    return out


def browser_condition_inputs() -> dict[str, str] | None:
    """Browser's ``ConditionInputs`` names; RobotCode doesn't check enum arguments."""
    try:
        from Browser.utils.data_types import ConditionInputs
    except Exception:
        return None
    return {normalize(m.name): m.name.replace("_", " ").title() for m in ConditionInputs}


# --------------------------------------------------------------------------
# Allowlist
# --------------------------------------------------------------------------


@dataclass
class AllowEntry:
    skill: str
    file: str
    keyword: str
    reason: str
    used: bool = False

    def matches(self, f: Finding) -> bool:
        return (
            self.skill == f.skill
            and self.file == f.file
            and normalize(self.keyword) == normalize(f.keyword)
        )


def load_allowlist(path: Path | None) -> list[AllowEntry]:
    if path is None or not path.exists():
        return []
    if tomllib is None:
        print("ERROR: reading the allowlist needs Python 3.11+ (tomllib)", file=sys.stderr)
        sys.exit(2)
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    entries = []
    for i, item in enumerate(raw.get("allow", [])):
        missing = [k for k in ("skill", "file", "keyword", "reason") if not str(item.get(k, "")).strip()]
        if missing:
            print(f"ERROR: allowlist entry #{i + 1} is missing {', '.join(missing)}", file=sys.stderr)
            sys.exit(2)
        entries.append(AllowEntry(skill_key(item["skill"]), item["file"], item["keyword"], item["reason"]))
    return entries


def skill_key(dir_name: str) -> str:
    """``rf-browser`` -> ``browser`` (skill dirs are named by their rf-<topic> id)."""
    return dir_name.removeprefix("rf-")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify that library skills only use existing, non-deprecated keywords.")
    parser.add_argument("--skills-root", action="append",
                        help="directory containing skill dirs; repeatable "
                             "(default: every <repo>/plugins/*/skills)")
    parser.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST),
                        help="TOML allowlist ([[allow]] skill/file/keyword/reason); '' disables it")
    parser.add_argument("--require-all", action="store_true",
                        help="fail when a skill is skipped because its library is not installed")
    args = parser.parse_args(argv)

    roots = ([Path(r) for r in args.skills_root] if args.skills_root
             else sorted(p for p in (REPO_ROOT / "plugins").glob("*/skills") if p.is_dir()))
    for root in roots:
        if not root.is_dir():
            print(f"ERROR: skills root not found: {root}", file=sys.stderr)
            return 2
    allow = load_allowlist(Path(args.allowlist) if args.allowlist else None)

    failed = False
    summaries: list[str] = []
    checked_skills: set[str] = set()
    for skill_dir in sorted((p for root in roots for p in root.iterdir() if p.is_dir()), key=lambda p: p.name):
        key = skill_key(skill_dir.name)
        if key not in SKILL_LIBRARIES:
            continue
        if robotcode_keywords(SKILL_LIBRARIES[key]) is None:
            summaries.append(f"{key}: skipped (library not installed: {SKILL_LIBRARIES[key]})")
            failed = failed or args.require_all
            continue
        checked_skills.add(key)
        conditions = browser_condition_inputs() if key == "browser" else None
        findings, nfiles = check_skill(key, skill_dir, SKILL_LIBRARIES[key], conditions)
        reported = 0
        for f in sorted(findings, key=lambda f: (f.file, f.line, f.kind, f.keyword)):
            entry = next((e for e in allow if e.matches(f)), None)
            if entry:
                entry.used = True
                continue
            print(f.format())
            reported += 1
        failed = failed or reported > 0
        summaries.append(f"{key}: checked {nfiles} files, {reported} findings")

    for entry in allow:
        if not entry.used and (entry.skill in checked_skills or entry.skill not in SKILL_LIBRARIES):
            print(f"STALE allowlist entry: skill={entry.skill} file={entry.file} "
                  f"keyword={entry.keyword!r} matches no call")
            failed = True

    print("--")
    for line in summaries:
        print(line)
    print("RESULT: FAIL" if failed else "RESULT: OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
