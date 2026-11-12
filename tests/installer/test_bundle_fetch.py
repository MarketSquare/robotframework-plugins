"""bundle.fetch(): snapshots of a repository ref (spec installer-python-api; public-bundle-api 4.1-4.3).

A fake GitHub on 127.0.0.1 serves the two endpoints fetch() uses, so the
suite never touches the real network (except the opt-in ``network`` test).
"""
from __future__ import annotations

import io
import json
import socket
import tarfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from robotframework_plugins import _snapshot, bundle

SHA = "a" * 40
OTHER = "b" * 40


def _plugin(files: dict[str, bytes], name: str, *, status: str = "active", skill: bool = True,
            manifest_extra: str = "") -> None:
    files[f"plugins/{name}/catalog.yaml"] = (
        f"name: {name}\nsummary: The {name} plugin.\ntier: verified\nstatus: {status}\n"
        f"libraries: []\nrobotframework: \">=7.0\"\n{manifest_extra}").encode()
    files[f"plugins/{name}/.claude-plugin/plugin.json"] = json.dumps({"name": name, "version": "1.2.3"}).encode()
    if skill:
        files[f"plugins/{name}/skills/{name}-skill/SKILL.md"] = b"---\nname: x\ndescription: y\n---\n"
        files[f"plugins/{name}/skills/{name}-skill/references/a.md"] = b"ref"
    files[f"plugins/{name}/tests/test_x.py"] = b"raise SystemExit('never extracted')"


def _tree() -> dict[str, bytes]:
    files: dict[str, bytes] = {"README.md": b"repo"}
    _plugin(files, "rf-web")
    _plugin(files, "rf-core")
    _plugin(files, "rf-old", status="deprecated")
    _plugin(files, "rf-agentskills", skill=False, manifest_extra="bundle: [rf-core, rf-web]\n")
    return files


def _tarball(files: dict[str, bytes], sha: str = SHA, extra=None) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        top = f"robotframework-plugins-{sha}"
        for name, data in files.items():
            info = tarfile.TarInfo(f"{top}/{name}")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        if extra:
            extra(tf, top)
    return buf.getvalue()


class FakeGitHub:
    def __init__(self) -> None:
        self.refs: dict[str, str] = {"main": SHA}
        self.archives: dict[str, bytes] = {SHA: _tarball(_tree())}
        self.requests: list[str] = []
        self.delay = 0.0
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args) -> None:
                pass

            def do_GET(self) -> None:
                fake.requests.append(self.path)
                time.sleep(fake.delay)
                prefix = f"/repos/{_snapshot.REPOSITORY}/commits/"
                if self.path.startswith(prefix):
                    sha = fake.refs.get(self.path[len(prefix):])
                    body = sha.encode() if sha else b'{"message": "No commit found"}'
                    self._send(200 if sha else 422, body)
                elif self.path.startswith(f"/{_snapshot.REPOSITORY}/tar.gz/"):
                    data = fake.archives.get(self.path.rsplit("/", 1)[1])
                    self._send(200 if data else 404, data or b"")
                else:
                    self._send(404, b"")

            def _send(self, code: int, body: bytes) -> None:
                self.send_response(code)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def downloads(self) -> int:
        return sum("/tar.gz/" in r for r in self.requests)


@pytest.fixture
def github(monkeypatch: pytest.MonkeyPatch):
    fake = FakeGitHub()
    monkeypatch.setattr(_snapshot, "GITHUB_API", fake.url)
    monkeypatch.setattr(_snapshot, "CODELOAD", fake.url)
    yield fake
    fake.server.shutdown()


@pytest.fixture
def cache(tmp_path: Path) -> Path:
    return tmp_path / "cache"


def _block_network(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    attempts: list[str] = []

    def refuse(*args, **kwargs):
        attempts.append(repr(args[:2]))
        raise ConnectionRefusedError("network blocked by the test")

    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    return attempts


def test_snapshot_of_main(github: FakeGitHub, cache: Path) -> None:
    snap = bundle.fetch("main", cache_dir=cache)
    assert (snap.ref, snap.commit) == ("main", SHA)
    dirs = snap.skills_dirs()
    assert list(dirs) == ["rf-core", "rf-web"]  # rf-core first; bundle and deprecated left out
    for path in dirs.values():
        assert path.is_dir() and any(path.glob("*/SKILL.md"))
        assert path.is_relative_to(cache.resolve())
    # Plugin tests/ are not extracted, as in the wheel.
    assert not (snap.path / "plugins" / "rf-web" / "tests").exists()
    assert json.loads((snap.path / "snapshot.json").read_text())["commit"] == SHA


def test_same_interface_as_the_bundle(github: FakeGitHub, cache: Path) -> None:
    snap = bundle.fetch("main", cache_dir=cache)
    entries = {p["name"]: p for p in snap.catalog()}
    assert set(entries) == {"rf-agentskills", "rf-core", "rf-old", "rf-web"}
    assert set(entries["rf-web"]) == set(bundle.catalog()[0])
    assert entries["rf-web"]["robotframework"] == ">=7.0"
    assert entries["rf-agentskills"]["bundle"] is True
    assert json.loads((snap.path / "catalog.json").read_text())["format"] == bundle.CATALOG_FORMAT
    snap.catalog().clear()
    assert len(snap.catalog()) == 4


def test_second_fetch_reuses_the_cache(github: FakeGitHub, cache: Path) -> None:
    first = bundle.fetch("main", cache_dir=cache)
    second = bundle.fetch("main", cache_dir=cache)
    assert github.downloads() == 1
    assert (first.commit, first.path, first.skills_dirs()) == (second.commit, second.path, second.skills_dirs())
    assert not [p for p in cache.iterdir() if p.name.startswith(".tmp-")]


def test_commit_sha_offline(github: FakeGitHub, cache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle.fetch("main", cache_dir=cache)
    attempts = _block_network(monkeypatch)
    snap = bundle.fetch(SHA.upper(), cache_dir=cache)
    assert snap.commit == SHA and snap.skills_dirs()
    assert attempts == []


def test_network_down(cache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    with pytest.raises(bundle.FetchError, match="resolving ref 'main' failed"):
        bundle.fetch("main", cache_dir=cache)
    with pytest.raises(bundle.FetchError, match="downloading"):
        bundle.fetch(OTHER, cache_dir=cache)
    assert bundle.skills_dirs()  # the bundled copy is unaffected
    assert not cache.exists() or not any(cache.iterdir())


def test_unknown_ref(github: FakeGitHub, cache: Path) -> None:
    with pytest.raises(bundle.FetchError, match="ref 'stable' not found"):
        bundle.fetch(cache_dir=cache)


def test_timeout(github: FakeGitHub, cache: Path) -> None:
    github.delay = 1.0
    with pytest.raises(bundle.FetchError, match="failed"):
        bundle.fetch("main", cache_dir=cache, timeout=0.2)


def _add_parent_entry(tf: tarfile.TarFile, top: str) -> None:
    info = tarfile.TarInfo(f"{top}/../outside.txt")
    info.size = 1
    tf.addfile(info, io.BytesIO(b"x"))


def _add_symlink(tf: tarfile.TarFile, top: str) -> None:
    info = tarfile.TarInfo(f"{top}/plugins/rf-web/skills/link")
    info.type = tarfile.SYMTYPE
    info.linkname = "/etc/passwd"
    tf.addfile(info)


@pytest.mark.parametrize(("extra", "message"), [
    (_add_parent_entry, "leaves the snapshot folder"),
    (_add_symlink, "is a link or a special file"),
])
def test_unsafe_archive_refused(github: FakeGitHub, cache: Path, tmp_path: Path, extra, message: str) -> None:
    github.archives[SHA] = _tarball(_tree(), extra=extra)
    with pytest.raises(bundle.FetchError, match=message):
        bundle.fetch("main", cache_dir=cache)
    assert not (cache / SHA).exists()
    assert not (tmp_path / "outside.txt").exists() and not (cache.parent / "outside.txt").exists()
    assert not [p for p in cache.iterdir() if p.name.startswith(".tmp-")]


def test_broken_plugin_manifest_refused(github: FakeGitHub, cache: Path) -> None:
    files = _tree()
    files["plugins/rf-web/catalog.yaml"] = b"name: rf-web\nsummary: x\ntier: verified\n"
    github.archives[SHA] = _tarball(files)
    with pytest.raises(bundle.FetchError, match=r"rf-web: catalog\.yaml lacks status"):
        bundle.fetch("main", cache_dir=cache)
    assert not (cache / SHA).exists()


def test_archive_without_plugins_refused(github: FakeGitHub, cache: Path) -> None:
    github.archives[SHA] = _tarball({"README.md": b"x"})
    with pytest.raises(bundle.FetchError, match="no plugins/ folder"):
        bundle.fetch("main", cache_dir=cache)


def test_the_installer_never_fetches() -> None:
    """Only bundle.py may import _snapshot; the CLI and adapters never do."""
    pkg = Path(bundle.__file__).parent
    offenders = [p.relative_to(pkg).as_posix() for p in pkg.rglob("*.py")
                 if p.name not in ("bundle.py", "_snapshot.py") and "_snapshot" in p.read_text(encoding="utf-8")]
    assert offenders == []


@pytest.mark.network
def test_fetch_main_from_github(tmp_path: Path) -> None:
    """Manual check before a release: `pytest -m network`."""
    snap = bundle.fetch("main", cache_dir=tmp_path)
    assert len(snap.commit) == 40
    dirs = snap.skills_dirs()
    assert next(iter(dirs)) == "rf-core"
    for path in dirs.values():
        assert any(path.glob("*/SKILL.md"))
