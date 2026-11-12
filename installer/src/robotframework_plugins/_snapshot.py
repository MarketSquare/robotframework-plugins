"""Snapshots of the plugins at a ref of the repository (``bundle.fetch()``).

The only code in the package that uses the network, and only when
``fetch()`` is called. The installer's commands never import it.

1. Resolve the ref to a commit SHA (a full SHA is taken as is).
2. Reuse ``<cache>/<sha>/`` when a finished snapshot is there.
3. Download the commit's archive from GitHub, with a timeout and size caps.
4. Check every archive entry, and extract ``plugins/`` by hand: only regular
   files and directories, no absolute paths, no ``..``.
5. Build the catalogue with the wheel's rules (``_catalog``), then move the
   finished folder into the cache in one step.

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
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from . import __version__, _catalog

REPOSITORY = "MarketSquare/robotframework-plugins"
#: Base URLs; tests point them at a local server.
GITHUB_API = "https://api.github.com"
CODELOAD = "https://codeload.github.com"
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


def fetch(ref: str = "stable", *, cache_dir: str | os.PathLike[str] | None = None,
          timeout: float = 30.0) -> Snapshot:
    ref = str(ref).strip()
    if not ref:
        raise FetchError("ref is empty")
    cache = Path(cache_dir) if cache_dir is not None else default_cache_dir()
    sha = ref.lower() if _SHA.fullmatch(ref.lower()) else None
    if sha is None:
        sha = _resolve(ref, timeout)
    hit = _cached(cache, sha, ref)
    if hit is not None:
        return hit
    return _build(ref, sha, cache, timeout)


def _cached(cache: Path, sha: str, ref: str) -> Snapshot | None:
    folder = cache / sha
    if (folder / _DONE).is_file() and (folder / "catalog.json").is_file():
        return Snapshot(ref=ref, commit=sha, path=folder.resolve())
    return None


def _request(url: str, accept: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"Accept": accept, "User-Agent": f"robotframework-plugins/{__version__}"})


def _resolve(ref: str, timeout: float) -> str:
    url = f"{GITHUB_API}/repos/{REPOSITORY}/commits/{urllib.parse.quote(ref, safe='/')}"
    try:
        with urllib.request.urlopen(_request(url, "application/vnd.github.sha"), timeout=timeout) as resp:
            body = resp.read(200).decode("ascii", "replace").strip()
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 422):
            raise FetchError(f"ref {ref!r} not found in {REPOSITORY}") from exc
        raise FetchError(f"resolving ref {ref!r} failed: HTTP {exc.code}") from exc
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        raise FetchError(f"resolving ref {ref!r} failed: {_reason(exc)}") from exc
    if not _SHA.fullmatch(body):
        raise FetchError(f"resolving ref {ref!r} returned no commit SHA")
    return body


def _reason(exc: BaseException) -> str:
    reason = getattr(exc, "reason", None) or exc
    return f"{type(reason).__name__}: {reason}"


def _build(ref: str, sha: str, cache: Path, timeout: float) -> Snapshot:
    try:
        cache.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix=f".tmp-{sha[:12]}-", dir=cache))
    except OSError as exc:
        raise FetchError(f"cache folder {cache} is not writable: {exc}") from exc
    try:
        archive = work / "archive.tar.gz"
        _download(sha, archive, timeout)
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
        }, indent=2) + "\n", encoding="utf-8")
        target = cache / sha
        try:
            os.replace(snap, target)
        except OSError:
            # Another process finished the same snapshot first: use its folder.
            hit = _cached(cache, sha, ref)
            if hit is None:
                raise
            return hit
        return Snapshot(ref=ref, commit=sha, path=target.resolve())
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _download(sha: str, dest: Path, timeout: float) -> None:
    url = f"{CODELOAD}/{REPOSITORY}/tar.gz/{sha}"
    size = 0
    try:
        with urllib.request.urlopen(_request(url, "application/octet-stream"), timeout=timeout) as resp, \
                dest.open("wb") as out:
            while chunk := resp.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_ARCHIVE_BYTES:
                    raise FetchError(f"archive of {sha[:12]} is larger than {MAX_ARCHIVE_BYTES // 2**20} MB")
                out.write(chunk)
    except urllib.error.HTTPError as exc:
        raise FetchError(f"downloading {sha[:12]} failed: HTTP {exc.code}") from exc
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        raise FetchError(f"downloading {sha[:12]} failed: {_reason(exc)}") from exc


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
