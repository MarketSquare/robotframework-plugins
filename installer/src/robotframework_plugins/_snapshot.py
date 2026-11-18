"""Snapshots of the plugins at a ref of the repository (``bundle.fetch()``).

The only code in the package that uses the network, and only when
``fetch()`` is called. The installer's commands never import it.

1. Resolve the ref to a commit SHA (a full SHA is taken as is).
2. Reuse ``<cache>/<sha>/`` when a finished snapshot in the running
   catalogue format is there.
3. Download the commit's archive from GitHub or the configured source, with a
   timeout and size caps. A token goes only to the source's own host.
4. Check every archive entry, and extract ``plugins/`` by hand: only regular
   files and directories, no absolute paths, no ``..``.
5. Build the catalogue with the wheel's rules (``_catalog``), then move the
   finished folder into the cache in one step, replacing a stale one.

Nothing from the snapshot is imported or run.
"""

from __future__ import annotations

import copy
import datetime as _dt
import http.client
import json
import os
import re
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from . import __version__, _catalog

REPOSITORY = "MarketSquare/robotframework-plugins"
#: Base URLs of the default source; tests point them at a local server.
GITHUB_API = "https://api.github.com"
CODELOAD = "https://codeload.github.com"
#: Environment settings for a mirror and a token (README, "fetch() and the network").
SOURCE_ENV = "ROBOTFRAMEWORK_PLUGINS_SOURCE"
TOKEN_ENV = "ROBOTFRAMEWORK_PLUGINS_TOKEN"
_LOOPBACK = ("localhost", "127.0.0.1", "::1")
#: Caps on the compressed download and on what it may expand to.
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_EXTRACTED_BYTES = 512 * 1024 * 1024
_SHA = re.compile(r"[0-9a-f]{40}")
_DONE = "snapshot.json"


class FetchError(RuntimeError):
    """A snapshot couldn't be fetched or failed its checks; the cache is unchanged."""


@dataclass(frozen=True)
class Snapshot:
    """The plugins at one commit of the repository, extracted in the cache."""

    ref: str
    commit: str
    path: Path
    #: Catalogue format the snapshot was built with; None for snapshots from before 2026.11.0.
    catalog_format: int | None = None

    def catalog(self) -> list[dict[str, Any]]:
        """The snapshot's plugins (active and deprecated), as ``bundle.catalog()``."""
        doc = json.loads((self.path / "catalog.json").read_text(encoding="utf-8"))
        return copy.deepcopy(list(doc.get("plugins", [])))

    def skills_dirs(self) -> dict[str, Path]:
        """``{plugin: skills folder}`` of the snapshot, as ``bundle.skills_dirs()``."""
        return _catalog.skill_dirs(self.catalog(), self.path)


def default_cache_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "robotframework-plugins" / "snapshots"


@dataclass(frozen=True)
class _Source:
    """Where requests go: the default github.com, or a GitHub-compatible API."""

    api: str
    token: str | None
    default: bool

    @property
    def where(self) -> str:
        """`` at <host>`` for a configured source, for error messages; never the token."""
        if self.default:
            return ""
        parts = urllib.parse.urlsplit(self.api)  # hostname and port only: netloc may hold user:password
        return f" at {parts.hostname}" + (f":{parts.port}" if parts.port else "")


def _source(source: str | None, token: str | None) -> _Source:
    configured = (source if source is not None else os.environ.get(SOURCE_ENV, "")).strip().rstrip("/")
    default = not configured
    api = GITHUB_API if default else configured
    if token is None:
        # GITHUB_TOKEN is a GitHub credential: never send it to a mirror.
        token = os.environ.get(TOKEN_ENV) or (os.environ.get("GITHUB_TOKEN") if default else None)
    token = (token or "").strip() or None
    parts = urllib.parse.urlsplit(api)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise FetchError(f"source {api!r} is not an http(s) URL")
    if token and parts.scheme == "http" and parts.hostname not in _LOOPBACK:
        raise FetchError(f"refusing to send a token over plain HTTP to {parts.hostname}; use an https source")
    return _Source(api=api, token=token, default=default)


def fetch(ref: str = "stable", *, source: str | None = None, token: str | None = None,
          cache_dir: str | os.PathLike[str] | None = None, timeout: float = 30.0) -> Snapshot:
    """Snapshot of the plugins at ``ref`` (branch, tag or full commit SHA) of the repository.

    ``source`` is the base URL of a GitHub-compatible API (GitHub Enterprise,
    an artifact manager's GitHub remote); default ``ROBOTFRAMEWORK_PLUGINS_SOURCE``,
    then github.com. ``token`` is sent as a bearer token to that source only;
    default ``ROBOTFRAMEWORK_PLUGINS_TOKEN``, then ``GITHUB_TOKEN`` for github.com.
    ``token=""`` sends none. Raises :class:`FetchError` on any failure.
    """
    ref = str(ref).strip()
    if not ref:
        raise FetchError("ref is empty")
    src = _source(source, token)
    cache = Path(cache_dir) if cache_dir is not None else default_cache_dir()
    sha = ref.lower() if _SHA.fullmatch(ref.lower()) else None
    if sha is None:
        sha = _resolve(ref, timeout, src)
    hit = _cached(cache, sha, ref)
    if hit is not None:
        return hit
    return _build(ref, sha, cache, timeout, src)


def _cached(cache: Path, sha: str, ref: str) -> Snapshot | None:
    """A finished snapshot of ``sha`` in the running catalogue format, else None."""
    folder = cache / sha
    if not ((folder / _DONE).is_file() and (folder / "catalog.json").is_file()):
        return None
    try:
        recorded = json.loads((folder / _DONE).read_text(encoding="utf-8")).get("catalog_format")
    except (OSError, ValueError, AttributeError):
        return None
    if recorded != _catalog.CATALOG_FORMAT:
        return None
    return Snapshot(ref=ref, commit=sha, path=folder.resolve(), catalog_format=recorded)


def _request(url: str, accept: str, token: str | None = None) -> urllib.request.Request:
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": f"robotframework-plugins/{__version__}"})
    if token:
        # Unredirected: urllib doesn't copy it to the host a redirect points to.
        req.add_unredirected_header("Authorization", f"Bearer {token}")
    return req


def _resolve(ref: str, timeout: float, src: _Source) -> str:
    url = f"{src.api}/repos/{REPOSITORY}/commits/{urllib.parse.quote(ref, safe='/')}"
    try:
        with urllib.request.urlopen(_request(url, "application/vnd.github.sha", src.token), timeout=timeout) as resp:
            body = resp.read(200).decode("ascii", "replace").strip()
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 422):
            hint = ("; every release moves 'stable', so use 'latest' or a release tag such as 'v5.0.0' instead"
                    if ref == "stable" else "")
            raise FetchError(f"ref {ref!r} not found in {REPOSITORY}{src.where}{hint}") from exc
        raise FetchError(f"resolving ref {ref!r}{src.where} failed: HTTP {exc.code}") from exc
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        raise FetchError(f"resolving ref {ref!r}{src.where} failed: {_reason(exc)}") from exc
    if not _SHA.fullmatch(body):
        raise FetchError(f"resolving ref {ref!r} returned no commit SHA")
    return body


def _reason(exc: BaseException) -> str:
    reason = getattr(exc, "reason", None) or exc
    return f"{type(reason).__name__}: {reason}"


def _build(ref: str, sha: str, cache: Path, timeout: float, src: _Source) -> Snapshot:
    try:
        cache.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix=f".tmp-{sha[:12]}-", dir=cache))
    except OSError as exc:
        raise FetchError(f"cache folder {cache} is not writable: {exc}") from exc
    try:
        archive = work / "archive.tar.gz"
        _download(sha, archive, timeout, src)
        snap = work / "snapshot"
        _extract_plugins(archive, snap)
        try:
            entries = _catalog.catalog_entries(snap / "plugins")
        except _catalog.CatalogError as exc:
            raise FetchError(f"snapshot {sha[:12]}: {exc}") from exc
        (snap / "catalog.json").write_text(_catalog.catalog_document(entries), encoding="utf-8")
        (snap / _DONE).write_text(json.dumps({
            "repository": REPOSITORY, "ref": ref, "commit": sha,
            "fetched_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),  # noqa: UP017 (3.10)
            "catalog_format": _catalog.CATALOG_FORMAT,
            "built_by": f"robotframework-plugins {__version__}",
        }, indent=2) + "\n", encoding="utf-8")
        target = cache / sha
        try:
            _install(snap, target, cache, sha)
        except OSError as exc:
            # Another process finished the same snapshot first: use its folder.
            hit = _cached(cache, sha, ref)
            if hit is None:
                raise FetchError(f"storing snapshot {sha[:12]} in {cache} failed: {exc}") from exc
            return hit
        return Snapshot(ref=ref, commit=sha, path=target.resolve(), catalog_format=_catalog.CATALOG_FORMAT)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _install(snap: Path, target: Path, cache: Path, sha: str) -> None:
    """Move the finished ``snap`` to ``target``; a stale snapshot there goes only once the move worked."""
    if _cached(cache, sha, "") is not None:
        raise OSError("a current snapshot appeared meanwhile")
    stale = None
    if target.exists():
        stale = cache / f".stale-{sha[:12]}-{uuid.uuid4().hex[:8]}"
        os.replace(target, stale)
    try:
        os.replace(snap, target)
    except OSError:
        if stale is not None and not target.exists():
            os.replace(stale, target)
            stale = None
        raise
    finally:
        if stale is not None:
            shutil.rmtree(stale, ignore_errors=True)


def _download(sha: str, dest: Path, timeout: float, src: _Source) -> None:
    # github.com: the public archive host needs no API quota and no token.
    if src.default:
        req = _request(f"{CODELOAD}/{REPOSITORY}/tar.gz/{sha}", "application/octet-stream")
    else:
        req = _request(f"{src.api}/repos/{REPOSITORY}/tarball/{sha}", "application/octet-stream", src.token)
    size = 0
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp, \
                dest.open("wb") as out:
            while chunk := resp.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_ARCHIVE_BYTES:
                    raise FetchError(f"archive of {sha[:12]} is larger than {MAX_ARCHIVE_BYTES // 2**20} MB")
                out.write(chunk)
    except urllib.error.HTTPError as exc:
        raise FetchError(f"downloading {sha[:12]}{src.where} failed: HTTP {exc.code}") from exc
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        raise FetchError(f"downloading {sha[:12]}{src.where} failed: {_reason(exc)}") from exc


def _safe_parts(name: str) -> tuple[str, ...]:
    path = PurePosixPath(name.replace("\\", "/"))
    parts = tuple(p for p in path.parts if p not in ("", "."))
    if path.is_absolute() or ".." in parts or (parts and ":" in parts[0]):
        raise FetchError(f"archive entry {name!r} leaves the snapshot folder")
    return parts


def _extract_plugins(archive: Path, dest: Path) -> None:
    """Check every entry, then write ``<top>/plugins/**`` (minus plugin tests/evals) to ``dest/plugins``."""
    try:
        with tarfile.open(archive, "r:gz") as tf:
            members = tf.getmembers()
            _check_members(members)
            written = _write_plugins(tf, members, dest)
    except (tarfile.TarError, EOFError) as exc:
        raise FetchError(f"archive is not a readable gzip tarball: {exc}") from exc
    except OSError as exc:
        raise FetchError(f"extracting the archive failed: {exc}") from exc
    if not written or not (dest / "plugins").is_dir():
        raise FetchError("archive has no plugins/ folder")


def _check_members(members: list[tarfile.TarInfo]) -> None:
    total = 0
    for m in members:
        _safe_parts(m.name)
        if not (m.isfile() or m.isdir()):
            raise FetchError(f"archive entry {m.name!r} is a link or a special file")
        total += m.size if m.isfile() else 0
    if total > MAX_EXTRACTED_BYTES:
        raise FetchError(f"archive expands to more than {MAX_EXTRACTED_BYTES // 2**20} MB")


def _write_plugins(tf: tarfile.TarFile, members: list[tarfile.TarInfo], dest: Path) -> int:
    written = 0
    for m in members:
        parts = _safe_parts(m.name)
        # <top>/plugins/<plugin>/...; a plugin's own tests/ and evals/ stay out.
        if len(parts) < 3 or parts[1] != "plugins":
            continue
        if len(parts) > 3 and parts[3] in _catalog.PLUGIN_ONLY_DIRS:
            continue
        target = dest.joinpath("plugins", *parts[2:])
        if m.isdir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        src = tf.extractfile(m)
        if src is None:
            raise FetchError(f"archive entry {m.name!r} can't be read")
        target.parent.mkdir(parents=True, exist_ok=True)
        with src, target.open("wb") as out:
            shutil.copyfileobj(src, out)
        written += 1
    return written
