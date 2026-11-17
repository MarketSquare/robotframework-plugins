"""Static keyword resolution for the ``keywords_resolve`` check.

Spec skill-eval-harness, "Static keyword resolution uses the installed
libraries". Used where a library cannot run on the CI runner (AppiumLibrary
without a device, PlatynUI without a desktop session), but installs and loads:

- ``robotcode analyze code`` resolves every call against the libraries in the
  grader environment. ``KeywordNotFound``, argument errors and failed imports
  fail the check.
- ``min_calls`` counts the library calls the tests and suite/test fixtures
  reach: a direct library call counts once, and a user-keyword call counts the
  library calls in that keyword's body, recursively (memoised; a keyword
  already being expanded adds nothing). User keywords that nothing calls add
  nothing, and standard-library calls never count. RobotCode has no call
  graph, so the walk over the parsed model stays here; the library keyword
  names come from ``robotcode doc keywords --format json``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..grader.robot_runner import RobotcodeMissingError, robotcode_binary

_STANDARD_LIBRARIES = frozenset(
    {
        "BuiltIn",
        "Collections",
        "DateTime",
        "Dialogs",
        "OperatingSystem",
        "Process",
        "Screenshot",
        "String",
        "Telnet",
        "XML",
    }
)
_GHERKIN = re.compile(r"^(given|when|then|and|but)\s+", re.IGNORECASE)


def normalize(name: str) -> str:
    return re.sub(r"[\s_]+", "", name).lower()


@dataclass(frozen=True)
class _KeywordSet:
    plain: frozenset[str]
    embedded: tuple[re.Pattern[str], ...]

    def matches(self, name: str) -> bool:
        if normalize(name) in self.plain:
            return True
        return any(p.fullmatch(name) for p in self.embedded)


def _embedded_pattern(name: str) -> re.Pattern[str] | None:
    if "${" not in name:
        return None
    try:
        from robot.running.arguments.embedded import EmbeddedArguments
    except ImportError:  # pragma: no cover - robot is a harness dependency
        return None
    emb = EmbeddedArguments.from_name(name)
    if emb is None:
        return None
    pattern: re.Pattern[str] = emb.name
    return pattern


def _keyword_set(names: list[str]) -> _KeywordSet:
    plain: set[str] = set()
    embedded: list[re.Pattern[str]] = []
    for n in names:
        pat = _embedded_pattern(n)
        if pat is not None:
            embedded.append(pat)
        else:
            plain.add(normalize(n))
    return _KeywordSet(frozenset(plain), tuple(embedded))


@lru_cache(maxsize=64)
def _library_keywords(library: str, cwd: str) -> tuple[str, ...] | None:
    """Keyword names of ``library`` from ``robotcode doc keywords``; None when it doesn't load."""
    robotcode = robotcode_binary()
    if robotcode is None:
        raise RobotcodeMissingError("robotcode is not installed")
    proc = subprocess.run([robotcode, "--format", "json", "doc", "keywords", library],
                          capture_output=True, text=True, check=False, timeout=180, cwd=cwd)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    return tuple(str(kw["name"]) for kw in data.get("keywords", []))


@dataclass(frozen=True)
class Diagnostic:
    path: str
    line: int
    code: str
    message: str
    severity: int


def analyze(targets: list[Path], cwd: Path, cache_dir: Path | None = None) -> list[Diagnostic]:
    """``robotcode --format json analyze code`` on ``targets``; diagnostics with 1-based lines.

    ``cache_dir`` keeps RobotCode's analysis cache out of the analysed folder.
    """
    robotcode = robotcode_binary()
    if robotcode is None:
        raise RobotcodeMissingError("robotcode is not installed")
    env = dict(os.environ)
    if cache_dir is not None:
        env["ROBOTCODE_CACHE_DIR"] = str(cache_dir)
    proc = subprocess.run([robotcode, "--format", "json", "analyze", "code", *[str(t) for t in targets]],
                          capture_output=True, text=True, check=False, timeout=600, cwd=cwd, env=env)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"robotcode analyze code gave no JSON: {(proc.stderr or proc.stdout)[-300:]}") from exc
    found = []
    for path, diags in (data.get("diagnostics") or {}).items():
        for d in diags:
            found.append(Diagnostic(str(path), int(d["range"]["start"]["line"]) + 1, str(d.get("code") or ""),
                                    str(d.get("message") or "").splitlines()[0], int(d.get("severity") or 0)))
    return found


def is_import_failure(diag: Diagnostic) -> bool:
    return diag.code == "DataError" and diag.message.startswith("Importing ")


# Owner of a call: None for a test or a suite/test fixture, else the index of
# the user keyword (in ``_Parsed.user_keywords``) whose body holds the call.
_Owner = int | None


@dataclass
class _Parsed:
    calls: list[tuple[str, str, _Owner]] = field(default_factory=list)  # (keyword, location, owner)
    user_keywords: list[str] = field(default_factory=list)
    libraries: list[str] = field(default_factory=list)
    resource_names: list[str] = field(default_factory=list)
    unresolved_imports: list[str] = field(default_factory=list)


def _make_visitor(path: Path, parsed: _Parsed, resources: list[Path]) -> Any:
    from robot.api.parsing import ModelVisitor

    rel = path.name
    owner: list[_Owner] = [None]

    def fixture(self: Any, node: Any) -> None:
        name = getattr(node, "name", None)
        if name and name.upper() != "NONE":
            parsed.calls.append((str(name), f"{rel}:{node.lineno}", owner[0]))

    class Visitor(ModelVisitor):  # type: ignore[misc]
        visit_SuiteSetup = fixture  # noqa: N815
        visit_SuiteTeardown = fixture  # noqa: N815
        visit_TestSetup = fixture  # noqa: N815
        visit_TestTeardown = fixture  # noqa: N815
        visit_Setup = fixture  # noqa: N815
        visit_Teardown = fixture  # noqa: N815

        def visit_LibraryImport(self, node: Any) -> None:  # noqa: N802
            parsed.libraries.append(str(node.name))

        def visit_ResourceImport(self, node: Any) -> None:  # noqa: N802
            raw = str(node.name).replace("${CURDIR}", str(path.parent))
            candidate = Path(raw) if Path(raw).is_absolute() else path.parent / raw
            if candidate.is_file():
                resources.append(candidate)
                parsed.resource_names.append(candidate.stem)
            else:
                parsed.unresolved_imports.append(f"Resource {node.name} ({rel})")

        def visit_Keyword(self, node: Any) -> None:  # noqa: N802
            parsed.user_keywords.append(str(node.name))
            owner[0] = len(parsed.user_keywords) - 1
            try:
                self.generic_visit(node)
            finally:
                owner[0] = None

        def visit_KeywordCall(self, node: Any) -> None:  # noqa: N802
            if node.keyword:
                parsed.calls.append((str(node.keyword), f"{rel}:{node.lineno}", owner[0]))

    return Visitor()


def _visit_file(path: Path, parsed: _Parsed, seen: set[Path]) -> None:
    from robot.api import get_model

    real = path.resolve()
    if real in seen:
        return
    seen.add(real)
    model = get_model(str(path)) if path.suffix == ".robot" else _resource_model(path)
    resources: list[Path] = []
    _make_visitor(path, parsed, resources).visit(model)
    for res in resources:
        _visit_file(res, parsed, seen)


def _resource_model(path: Path) -> Any:
    from robot.api import get_resource_model

    return get_resource_model(str(path))


@dataclass
class ResolutionResult:
    calls: int = 0
    library_calls: int = 0
    counted_library_calls: int = 0
    unknown: list[str] = field(default_factory=list)
    argument_errors: list[str] = field(default_factory=list)
    unresolved_imports: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    min_calls: int = 1
    parse_error: str = ""

    @property
    def ok(self) -> bool:
        return (
            not self.parse_error
            and not self.unknown
            and not self.argument_errors
            and not self.unresolved_imports
            and not self.missing_required
            and self.counted_library_calls >= self.min_calls
        )

    def summary(self) -> str:
        parts = [
            f"calls={self.calls} library_calls={self.library_calls}"
            f" counted_library_calls={self.counted_library_calls}"
        ]
        if self.parse_error:
            parts.append(f"parse error: {self.parse_error}")
        if self.missing_required:
            parts.append(f"required library not imported: {self.missing_required}")
        if self.unresolved_imports:
            parts.append(f"unresolved imports: {self.unresolved_imports}")
        if self.unknown:
            parts.append(f"unknown keywords (KeywordNotFound): {self.unknown[:10]}")
        if self.argument_errors:
            parts.append(f"argument errors: {self.argument_errors[:10]}")
        if self.counted_library_calls < self.min_calls:
            parts.append(
                f"expected >= {self.min_calls} library keyword calls"
                " (counted through user keywords)"
            )
        return "; ".join(parts)


def _library_sets(imported: list[str], cwd: Path) -> dict[str, _KeywordSet]:
    """Keyword sets of the imported libraries that load; import failures come from the analysis."""
    sets: dict[str, _KeywordSet] = {}
    for lib in imported:
        if lib in sets:
            continue
        names = _library_keywords(lib, str(cwd))
        if names is not None:
            sets[lib] = _keyword_set(list(names))
    return sets


def _candidates(raw: str, owners: set[str]) -> list[str]:
    name = _GHERKIN.sub("", raw)
    out = [name]
    if "." in name:
        prefix, _, rest = name.rpartition(".")
        if normalize(prefix) in owners:
            out.append(rest)
    return out


# What a call resolves to: ("user", keyword index), ("library", 1),
# ("standard", 0) or ("unknown", 0).
_Target = tuple[str, int]


def _resolve_calls(
    parsed: _Parsed, library_sets: dict[str, _KeywordSet], result: ResolutionResult
) -> None:
    user = [_keyword_set([n]) for n in parsed.user_keywords]
    owners = {normalize(n) for n in [*library_sets, *parsed.resource_names]}
    by_owner: dict[_Owner, list[_Target]] = {}
    for raw, _where, owner in parsed.calls:
        if raw.startswith(("${", "@{", "&{")):
            continue  # keyword name held in a variable: not statically resolvable
        result.calls += 1
        candidates = _candidates(raw, owners)
        target = _resolve_one(candidates, user, library_sets)
        if target[0] == "library":
            result.library_calls += 1
        by_owner.setdefault(owner, []).append(target)
    result.counted_library_calls = _count_from_roots(by_owner)


def _resolve_one(
    candidates: list[str], user: list[_KeywordSet], library_sets: dict[str, _KeywordSet]
) -> _Target:
    for idx, ks in enumerate(user):
        if any(ks.matches(c) for c in candidates):
            return ("user", idx)
    hit = next(
        (lib for lib, ks in library_sets.items() if any(ks.matches(c) for c in candidates)),
        None,
    )
    if hit is None:
        return ("unknown", 0)
    return ("standard", 0) if hit in _STANDARD_LIBRARIES else ("library", 1)


def _count_from_roots(by_owner: dict[_Owner, list[_Target]]) -> int:
    """Library calls reached from tests and fixtures, expanding user keywords."""
    memo: dict[int, int] = {}
    stack: set[int] = set()

    def weight(target: _Target) -> int:
        kind, value = target
        if kind == "library":
            return 1
        if kind == "user":
            return expand(value)
        return 0

    def expand(idx: int) -> int:
        if idx in memo:
            return memo[idx]
        if idx in stack:
            return 0  # recursion: the outer expansion already counts this body
        stack.add(idx)
        total = sum(weight(t) for t in by_owner.get(idx, []))
        stack.discard(idx)
        memo[idx] = total
        return total

    return sum(weight(t) for t in by_owner.get(None, []))


def resolve_suite_keywords(
    suite: Path,
    *,
    min_calls: int = 1,
    required_libraries: tuple[str, ...] = (),
    cwd: Path | None = None,
    cache_dir: Path | None = None,
) -> ResolutionResult:
    """Resolve every keyword call in ``suite`` (a file or a directory) with RobotCode.

    ``cwd`` is the project root whose ``robot.toml`` applies (default: the
    suite's folder). Raises :class:`RobotcodeMissingError` without robotcode.
    """
    result = ResolutionResult(min_calls=min_calls)
    files = sorted(p for p in suite.rglob("*.robot") if p.is_file()) if suite.is_dir() else [suite]
    if not files:
        result.parse_error = f"no .robot files under {suite}"
        return result
    root = cwd or (suite if suite.is_dir() else suite.parent)
    parsed = _Parsed()
    seen: set[Path] = set()
    try:
        for f in files:
            _visit_file(f, parsed, seen)
    except Exception as exc:  # robot parser errors are data errors for the agent
        result.parse_error = f"{type(exc).__name__}: {exc}"
        return result
    for diag in analyze([suite], root, cache_dir):
        where = f"{Path(diag.path).name}:{diag.line}"
        if diag.code == "KeywordNotFound":
            result.unknown.append(f"{diag.message} ({where})")
        elif is_import_failure(diag):
            result.unresolved_imports.append(f"{diag.message} ({where})")
        elif diag.code == "DataError":
            result.argument_errors.append(f"{diag.message} ({where})")
    imported = ["BuiltIn", *parsed.libraries]
    result.missing_required = [r for r in required_libraries if r not in imported]
    result.unresolved_imports.extend(parsed.unresolved_imports)
    library_sets = _library_sets(imported, root)
    _resolve_calls(parsed, library_sets, result)
    return result
