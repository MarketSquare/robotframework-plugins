#!/usr/bin/env python3
"""Run rf-desktop eval suites against the real Calculator on a Windows desktop.

The CI eval grades PlatynUI suites statically (``keywords_resolve`` and
``platynui_locators``). This manual check runs them: it collects the suites the
PlatynUI sessions of one downloaded eval run wrote, plus the skill's example,
screens each one, and runs the safe ones with a fresh Calculator and a time
limit. It reports pass counts per tier and arm and never writes baselines.

It must run in the logged-in desktop session, inside a venv that has
Robot Framework, robotframework-PlatynUI and platynui-cli; see
docs/ci/desktop-live-check.md. Downloaded artifacts are untrusted: run this
with ``python -I`` from outside the artifact directory.

Usage:
    python -I scripts/desktop-live-check.py <skill-eval-full-rf-desktop-RUN dir> [--out DIR]
    python -I scripts/desktop-live-check.py <dir> --list     # collect and screen only
"""

from __future__ import annotations

import argparse
import ast
import collections
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL_EXAMPLE = REPO / "plugins" / "rf-desktop" / "skills" / "rf-platynui" / "assets" / "examples" / "calculator.robot"

#: Libraries a collected suite may import. Process only for the skill's
#: example, which starts Calculator itself.
ALLOWED_LIBRARIES = frozenset({"PlatynUI.BareMetal", "BuiltIn", "Collections", "String"})
EXAMPLE_LIBRARIES = ALLOWED_LIBRARIES | {"Process"}
#: Keywords that run code or start processes (normalised names). File keywords
#: come from OperatingSystem, which no suite may import.
BANNED_KEYWORDS = frozenset(
    {"evaluate", "runprocess", "startprocess", "callmethod", "importlibrary", "importresource", "importvariables"}
)
#: The skill's example starts Calculator itself.
EXAMPLE_BANNED = BANNED_KEYWORDS - {"startprocess"}
#: Text that would make a Python expression (IF, Should Be True, ${{ }}) unsafe.
UNSAFE_TEXT = re.compile(r"\$\{\{|__|\bimport\b|\bopen\s*\(|\bos\.|\bsys\.|subprocess|\bexec\b|\beval\b")
READY_QUERY = "//control:Text[@Id='CalculatorResults']"


@dataclass
class Suite:
    tier: str  # narrow | partial | example
    arm: str  # baseline | treatment | example
    session: str
    path: Path
    skip_reason: str = ""
    passed: bool | None = None
    message: str = ""
    seconds: float = 0.0
    extra: list[Path] = field(default_factory=list)


def collect(artifact_dir: Path, suite_name: str = "calculator.robot") -> list[Suite]:
    """The task's suite (``workspace/tests/<suite_name>``) from each PlatynUI session under ``artifact_dir``.

    Only the file the task asks for: every workspace also holds the fixture's
    stub ``tests/example.robot``.
    """
    suites: list[Suite] = []
    for path in sorted(artifact_dir.rglob(f"workspace/tests/{suite_name}")):
        session = path.parents[2].name
        if "-platynui-" not in session:
            continue
        tier = session.split("-", 1)[0]
        if tier not in ("narrow", "partial"):
            continue
        arm = "baseline" if "-baseline-" in session else "treatment"
        suites.append(Suite(tier, arm, session, path))
    return suites


def _normalize(name: str) -> str:
    return re.sub(r"[\s_]+", "", name).lower()


def screen(
    path: Path,
    *,
    allowed: frozenset[str] = ALLOWED_LIBRARIES,
    banned: frozenset[str] = BANNED_KEYWORDS,
    root: Path | None = None,
) -> str:
    """Why ``path`` must not run ('' when it may). Resources are screened too and must stay under ``root``."""
    root = (root or path.parent).resolve()
    todo, seen = [path], set()
    while todo:
        current = todo.pop()
        real = current.resolve()
        if real in seen:
            continue
        seen.add(real)
        if not real.is_relative_to(root):
            return f"resource outside the session workspace: {current}"
        if not current.is_file():
            return f"resource not found: {current}"
        problem = _file_problem(current, allowed, banned, todo)
        if problem:
            return problem
    return ""


def _file_problem(path: Path, allowed: frozenset[str], banned: frozenset[str], resources: list[Path]) -> str:
    """The first reason ``path`` itself is unsafe; appends the resources it imports."""
    from robot.api import get_model, get_resource_model
    from robot.parsing.model.statements import (
        KeywordCall,
        LibraryImport,
        ResourceImport,
        Statement,
        VariablesImport,
    )

    model = get_model(str(path)) if path.suffix == ".robot" else get_resource_model(str(path))
    for node in ast.walk(model):
        if isinstance(node, LibraryImport) and str(node.name) not in allowed:
            return f"imports library {node.name}"
        if isinstance(node, VariablesImport):
            return f"imports variables {node.name}"
        if isinstance(node, ResourceImport) and node.name:
            resources.append(path.parent / str(node.name).replace("${CURDIR}", str(path.parent)))
        if (
            isinstance(node, KeywordCall)
            and node.keyword
            and _normalize(str(node.keyword).rpartition(".")[2]) in banned
        ):
            return f"calls {node.keyword} ({path.name}:{node.lineno})"
        if isinstance(node, Statement):
            problem = _expression_problem(node, path)
            if problem:
                return problem
    return ""


def _expression_problem(node: object, path: Path) -> str:
    """Text that could run Python (``${{ }}``, IF conditions, Should Be True), outside comments and docs."""
    from robot.api import Token

    if getattr(node, "type", None) in (Token.DOCUMENTATION, Token.METADATA):
        return ""
    for tok in getattr(node, "tokens", ()):
        if tok.type not in (Token.COMMENT, Token.SEPARATOR, Token.EOL) and UNSAFE_TEXT.search(tok.value):
            return f"unsafe expression {tok.value[:60]!r} ({path.name}:{tok.lineno})"
    return ""


def _cli() -> str:
    exe = Path(sys.executable).parent / ("platynui-cli.exe" if sys.platform == "win32" else "platynui-cli")
    return str(exe) if exe.is_file() else (shutil.which("platynui-cli") or "platynui-cli")


def _robot() -> list[str]:
    return [sys.executable, "-m", "robot"]


def stop_calculator() -> None:
    subprocess.run(["taskkill", "/im", "CalculatorApp.exe", "/f"], capture_output=True, check=False)


def start_calculator(ready_timeout: float) -> str:
    """Start Calculator and wait until its result display answers a query; '' when ready, else why not."""
    subprocess.Popen(["cmd", "/c", "start", "", "calc.exe"])
    deadline = time.monotonic() + ready_timeout
    last = "no query ran"
    while time.monotonic() < deadline:
        r = subprocess.run([_cli(), "query", READY_QUERY], capture_output=True, check=False)
        if b"CalculatorResults" in r.stdout:
            return ""
        out = (r.stdout or r.stderr).decode("utf-8", "replace").strip()
        last = f"exit {r.returncode}: {out[:120] or 'no output'}"
        time.sleep(1)
    return f"Calculator not ready after {ready_timeout:.0f} s (last query: {last})"


def result_of(output_xml: Path) -> tuple[bool, str]:
    try:
        root = ET.parse(output_xml).getroot()
    except (ET.ParseError, OSError):
        return False, "no output.xml (killed at the time limit?)"
    tests = root.findall(".//test")
    if not tests:
        status = root.find("suite/status")
        return False, "no tests: " + ((status.text or "") if status is not None else "")
    for test in tests:
        status = test.find("status")
        if status is not None and status.get("status") != "PASS":
            return False, ((status.text or "").strip().splitlines() or [""])[0][:160]
    return True, ""


def run_suite(suite: Suite, out: Path, *, timeout: float, ready_timeout: float) -> None:
    stop_calculator()
    time.sleep(1)
    if suite.arm != "example":
        why = start_calculator(ready_timeout)
        if why:
            suite.passed, suite.message = False, why
            return
    target = out / f"{suite.tier}__{suite.session}__{suite.path.stem}"
    started = time.monotonic()
    try:
        subprocess.run([*_robot(), "--outputdir", str(target), "--consolecolors", "off", str(suite.path)],
                       capture_output=True, timeout=timeout, check=False)
        suite.passed, suite.message = result_of(target / "output.xml")
    except subprocess.TimeoutExpired:
        suite.passed, suite.message = False, f"time limit {timeout:.0f} s"
    suite.seconds = time.monotonic() - started


def display_language() -> str:
    if sys.platform != "win32":
        return "n/a (not Windows)"
    import ctypes
    import locale

    langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()  # type: ignore[attr-defined]
    return locale.windows_locale.get(langid, hex(langid))


def _bucket(message: str) -> str:
    return re.sub(r"\d+(\.\d+)?", "N", re.sub(r"'[^']*'|\"[^\"]*\"", "Q", message))[:110]


def report(suites: list[Suite], *, ran: bool) -> str:
    lines = [f"display language: {display_language()}", ""]
    agg: dict[tuple[str, str], list[int]] = collections.defaultdict(lambda: [0, 0, 0])
    for s in suites:
        row = agg[(s.tier, s.arm)]
        row[0] += 1
        row[1] += bool(s.passed)
        row[2] += bool(s.skip_reason)
    lines.append(f"{'tier':8} {'arm':10} {'suites':>6} {'passed':>6} {'skipped':>7}")
    for (tier, arm), (n, p, sk) in sorted(agg.items()):
        lines.append(f"{tier:8} {arm:10} {n:6} {p if ran else '-':>6} {sk:7}")
    skipped = [s for s in suites if s.skip_reason]
    if skipped:
        lines += ["", "skipped (not run):"] + [f"  {s.session}: {s.skip_reason}" for s in skipped]
    if ran:
        top = collections.Counter(_bucket(s.message) for s in suites if s.passed is False and s.message)
        if top:
            lines += ["", "most common failures:"] + [f"  {n:3}  {m}" for m, n in top.most_common(8)]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("artifacts", type=Path, help="a downloaded skill-eval-full-rf-desktop-<run> directory")
    ap.add_argument("--out", type=Path, default=Path("live-check-results"), help="where robot writes its output")
    ap.add_argument("--timeout", type=float, default=150.0, help="seconds per suite (default 150)")
    ap.add_argument("--ready-timeout", type=float, default=30.0, help="seconds to wait for Calculator")
    ap.add_argument("--suite-name", default="calculator.robot", help="the file the task asks for")
    ap.add_argument("--list", action="store_true", help="collect and screen only; run nothing")
    args = ap.parse_args(argv)

    suites = collect(args.artifacts, args.suite_name)
    if SKILL_EXAMPLE.is_file():
        suites.append(Suite("example", "example", "skill example", SKILL_EXAMPLE))
    if not suites:
        print(f"no PlatynUI suites under {args.artifacts}", file=sys.stderr)
        return 1
    for s in suites:
        if s.arm == "example":
            s.skip_reason = screen(s.path, allowed=EXAMPLE_LIBRARIES, banned=EXAMPLE_BANNED)
        else:
            s.skip_reason = screen(s.path, root=s.path.parents[1])
    if not args.list:
        if sys.platform != "win32":
            print("the live check runs on a Windows desktop; use --list elsewhere", file=sys.stderr)
            return 2
        args.out.mkdir(parents=True, exist_ok=True)
        for s in (s for s in suites if not s.skip_reason):
            run_suite(s, args.out, timeout=args.timeout, ready_timeout=args.ready_timeout)
            print(f"{'PASS' if s.passed else 'FAIL'}  {s.tier:7} {s.session}  {s.message}", flush=True)
        stop_calculator()
    print(report(suites, ran=not args.list))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
