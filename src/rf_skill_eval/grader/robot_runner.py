"""Run Robot Framework suites and read their results through RobotCode.

Spec robotcode-first-tooling and skill-eval-harness, "Grader runs and reads
results through RobotCode": runs go through ``robotcode robot`` (so the
workspace's ``robot.toml`` applies) and counts and failure messages come from
``robotcode --format json results show``, not from parsing ``output.xml``.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from ..errors import GraderError

_log = logging.getLogger(__name__)


class RobotcodeMissingError(GraderError):
    """``robotcode`` is neither next to the interpreter nor on PATH."""


@dataclass(frozen=True)
class TestResult:
    name: str
    status: str
    message: str = ""


@dataclass(frozen=True)
class RobotResult:
    returncode: int | None
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int = 0
    tests: tuple[TestResult, ...] = field(default_factory=tuple)
    output_xml: Path | None = None
    output: str = ""
    timed_out: bool = False

    @property
    def all_passed(self) -> bool:
        return self.returncode == 0 and self.total_tests > 0 and self.failed_tests == 0

    def statuses(self) -> dict[str, str]:
        """Test name -> PASS/FAIL/SKIP/NOT RUN."""
        return {t.name: t.status for t in self.tests}

    def failures(self, limit: int = 3) -> list[str]:
        """``<test name>: <message>`` for the first failed tests."""
        return [f"{t.name}: {t.message.strip()[:120]}" for t in self.tests if t.status == "FAIL"][:limit]


def robotcode_binary() -> str | None:
    """``robotcode`` next to the running interpreter first, then PATH."""
    candidate = Path(sys.executable).parent / "robotcode"
    if candidate.is_file():
        return str(candidate)
    return shutil.which("robotcode")


def read_results(output_xml: Path, *, robotcode: str | None = None) -> tuple[dict[str, int], tuple[TestResult, ...]]:
    """Counts and per-test results of a finished run, from ``robotcode results show``.

    A missing or unreadable result file gives zero counts and no tests.
    """
    robotcode = robotcode or robotcode_binary()
    if robotcode is None:
        raise RobotcodeMissingError("robotcode is not installed (needed to read results)")
    empty = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
    if not output_xml.is_file():
        return empty, ()
    proc = subprocess.run(
        [robotcode, "--format", "json", "results", "show", "-o", str(output_xml), "--message-chars", "0"],
        capture_output=True, text=True, check=False, timeout=120, cwd=output_xml.parent,
    )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        _log.warning("robotcode results show could not read %s: %s", output_xml, proc.stderr.strip()[:200])
        return empty, ()
    counts = {k: int(data.get("counts", {}).get(k, 0)) for k in empty}
    tests = tuple(
        TestResult(str(t.get("name", "")), str(t.get("status", "")), str(t.get("message") or ""))
        for t in data.get("tests", [])
    )
    return counts, tests


def run_robot(
    targets: Sequence[Path | str],
    output_dir: Path,
    *,
    args: Sequence[str] = (),
    cwd: Path | None = None,
    dryrun: bool = False,
    timeout_seconds: int = 300,
    launcher: Sequence[str] | None = None,
) -> RobotResult:
    """Run ``robotcode robot`` on ``targets`` and read the results with robotcode.

    ``launcher`` replaces the ``robotcode`` executable, for example a ``uvx``
    command that runs robotcode with a pinned Robot Framework; results are
    still read with the harness's own ``robotcode``. Raises
    :class:`RobotcodeMissingError` when robotcode is not installed.
    """
    if not targets:
        raise GraderError("run_robot requires at least one target")
    robotcode = robotcode_binary()
    if robotcode is None:
        raise RobotcodeMissingError("robotcode is not installed (not next to the interpreter, not on PATH)")
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [*(launcher or [robotcode]), "robot", "--outputdir", str(output_dir),
           *(["--dryrun"] if dryrun else []), *[str(a) for a in args], *[str(t) for t in targets]]
    _log.info("Invoking grader: %s", " ".join(cmd))
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False,
                              timeout=timeout_seconds)
    except FileNotFoundError as exc:
        raise RobotcodeMissingError(f"{cmd[0]} is not installed") from exc
    except subprocess.TimeoutExpired:
        return RobotResult(None, 0, 0, 0, output=f"timed out after {timeout_seconds}s", timed_out=True)
    output_xml = output_dir / "output.xml"
    counts, tests = read_results(output_xml, robotcode=robotcode)
    return RobotResult(
        returncode=proc.returncode,
        total_tests=counts["total"],
        passed_tests=counts["passed"],
        failed_tests=counts["failed"],
        skipped_tests=counts["skipped"],
        tests=tests,
        output_xml=output_xml if output_xml.exists() else None,
        output=(proc.stdout or "") + "\n" + (proc.stderr or ""),
    )
