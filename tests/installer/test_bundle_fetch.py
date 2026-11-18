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
from robotframework_plugins import __version__, _snapshot, bundle

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
        #: (path, Authorization header or None) per request.
        self.auth: list[tuple[str, str | None]] = []
        #: When set, the tarball endpoint redirects here (``/<sha>`` is appended).
        self.redirect_to: str | None = None
        #: When set, every request is answered with this HTTP status.
        self.status: int | None = None
        self.delay = 0.0
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args) -> None:
                pass

            def do_GET(self) -> None:
                fake.requests.append(self.path)
                fake.auth.append((self.path, self.headers.get("Authorization")))
                time.sleep(fake.delay)
                if fake.status:
                    self._send(fake.status, b'{"message": "Bad credentials"}')
                    return
                prefix = f"/repos/{_snapshot.REPOSITORY}/commits/"
                tarball = f"/repos/{_snapshot.REPOSITORY}/tarball/"
                if self.path.startswith(tarball) and fake.redirect_to:
                    self.send_response(302)
                    self.send_header("Location", f"{fake.redirect_to}/{self.path[len(tarball):]}")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                elif self.path.startswith(tarball) or self.path.startswith("/blob/"):
                    data = fake.archives.get(self.path.rsplit("/", 1)[1])
                    self._send(200 if data else 404, data or b"")
                elif self.path.startswith(prefix):
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
        return sum("/tar.gz/" in r or "/tarball/" in r for r in self.requests)


@pytest.fixture(autouse=True)
def _no_source_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """A developer's or CI's own settings must not change what the tests send."""
    for name in (_snapshot.SOURCE_ENV, _snapshot.TOKEN_ENV, "GITHUB_TOKEN"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def mirror():
    """A second fake GitHub used as a configured source; github.com is not patched."""
    fake = FakeGitHub()
    yield fake
    fake.server.shutdown()


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
    assert set(entries) == {"rf-core", "rf-old", "rf-web"}
    assert set(entries["rf-web"]) == set(bundle.catalog()[0])
    assert entries["rf-web"]["robotframework"] == ">=7.0"
    assert entries["rf-web"]["bundle"] is False and entries["rf-web"]["bundled"] == []
    assert json.loads((snap.path / "catalog.json").read_text())["format"] == bundle.CATALOG_FORMAT
    snap.catalog().clear()
    assert len(snap.catalog()) == 3


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
    with pytest.raises(bundle.FetchError, match="ref 'nope' not found") as err:
        bundle.fetch("nope", cache_dir=cache)
    assert "release tag" not in str(err.value)


def test_missing_stable_names_the_alternatives(github: FakeGitHub, cache: Path) -> None:
    with pytest.raises(bundle.FetchError, match="ref 'stable' not found") as err:
        bundle.fetch(cache_dir=cache)
    assert "release tag such as 'v5.0.0'" in str(err.value) and "'main'" in str(err.value)
    assert "'latest'" not in str(err.value)
    assert "first plugin release" not in str(err.value)


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


def test_snapshot_passes_library_skills_through(github: FakeGitHub, cache: Path) -> None:
    """catalog-library-skills: a library with ``skills`` keeps them; one without gets no key."""
    files = _tree()
    files["plugins/rf-web/catalog.yaml"] = files["plugins/rf-web/catalog.yaml"].replace(
        b"libraries: []\n",
        b"libraries:\n"
        b"  - {name: Browser, package: robotframework-browser, versions: '>=20', skills: [rf-web-skill]}\n"
        b"  - {name: Other, package: robotframework-other, versions: '>=1'}\n")
    github.archives[SHA] = _tarball(files)
    web = next(p for p in bundle.fetch("main", cache_dir=cache).catalog() if p["name"] == "rf-web")
    libs = {lib["name"]: lib for lib in web["libraries"]}
    assert libs["Browser"]["skills"] == ["rf-web-skill"]
    assert "skills" not in libs["Other"]


# bundle-fetch-sources: mirror, token, catalogue format (#22, #23).

def test_mirror_as_argument(mirror: FakeGitHub, cache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_snapshot, "GITHUB_API", "https://github.invalid")
    monkeypatch.setattr(_snapshot, "CODELOAD", "https://github.invalid")
    snap = bundle.fetch("main", source=mirror.url + "/", cache_dir=cache)
    assert snap.commit == SHA and snap.skills_dirs()
    assert mirror.requests == [f"/repos/{_snapshot.REPOSITORY}/commits/main",
                               f"/repos/{_snapshot.REPOSITORY}/tarball/{SHA}"]


def test_mirror_from_the_environment(mirror: FakeGitHub, cache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_snapshot.SOURCE_ENV, mirror.url)
    assert bundle.fetch("main", cache_dir=cache).commit == SHA
    assert mirror.downloads() == 1


def test_token_reaches_the_source(mirror: FakeGitHub, cache: Path) -> None:
    bundle.fetch("main", source=mirror.url, token="t0k", cache_dir=cache)
    assert [auth for _, auth in mirror.auth] == ["Bearer t0k", "Bearer t0k"]


def test_token_from_the_environment(mirror: FakeGitHub, cache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_snapshot.TOKEN_ENV, "env-t0k")
    bundle.fetch("main", source=mirror.url, cache_dir=cache)
    assert {auth for _, auth in mirror.auth} == {"Bearer env-t0k"}


def test_empty_token_sends_none(mirror: FakeGitHub, cache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_snapshot.TOKEN_ENV, "env-t0k")
    bundle.fetch("main", source=mirror.url, token="", cache_dir=cache)
    assert {auth for _, auth in mirror.auth} == {None}


def test_redirect_does_not_carry_the_token(mirror: FakeGitHub, github: FakeGitHub, cache: Path) -> None:
    mirror.redirect_to = github.url + "/blob"
    snap = bundle.fetch("main", source=mirror.url, token="t0k", cache_dir=cache)
    assert snap.commit == SHA
    assert github.auth == [(f"/blob/{SHA}", None)]
    assert all(auth == "Bearer t0k" for _, auth in mirror.auth)


def test_github_token_stays_with_github(mirror: FakeGitHub, github: FakeGitHub, cache: Path,
                                        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "gh-t0k")
    bundle.fetch("main", source=mirror.url, cache_dir=cache)
    assert {auth for _, auth in mirror.auth} == {None}
    other = cache.parent / "other"
    bundle.fetch("main", cache_dir=other)
    assert (other / SHA).is_dir()
    # github.com: the API gets the token, the public archive host doesn't.
    assert github.auth == [(f"/repos/{_snapshot.REPOSITORY}/commits/main", "Bearer gh-t0k"),
                           (f"/{_snapshot.REPOSITORY}/tar.gz/{SHA}", None)]


def test_plain_http_refused_for_a_token(cache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = _block_network(monkeypatch)
    with pytest.raises(bundle.FetchError, match=r"plain HTTP to mirror\.example\.com") as err:
        bundle.fetch("main", source="http://mirror.example.com", token="t0k", cache_dir=cache)
    assert "t0k" not in str(err.value)
    assert attempts == []


@pytest.mark.parametrize("status", [401, 422])
def test_errors_never_contain_the_token(mirror: FakeGitHub, cache: Path, status: int) -> None:
    mirror.status = status
    with pytest.raises(bundle.FetchError) as err:
        bundle.fetch("main", source=mirror.url, token="t0k", cache_dir=cache)
    assert "t0k" not in str(err.value)
    assert "at 127.0.0.1:" in str(err.value)
    if status == 401:
        assert "HTTP 401" in str(err.value)


def test_errors_never_contain_url_credentials(mirror: FakeGitHub, cache: Path) -> None:
    with pytest.raises(bundle.FetchError) as err:
        bundle.fetch("main", source=mirror.url.replace("http://", "http://user:s3cret@"), cache_dir=cache)
    assert "s3cret" not in str(err.value)


def test_source_must_be_http(cache: Path) -> None:
    with pytest.raises(bundle.FetchError, match="not an http"):
        bundle.fetch("main", source="file:///etc", cache_dir=cache)


def test_snapshot_records_its_format(github: FakeGitHub, cache: Path) -> None:
    snap = bundle.fetch("main", cache_dir=cache)
    meta = json.loads((snap.path / "snapshot.json").read_text())
    assert snap.catalog_format == meta["catalog_format"] == bundle.CATALOG_FORMAT
    assert meta["built_by"] == f"robotframework-plugins {__version__}"
    assert bundle.fetch(SHA, cache_dir=cache).catalog_format == bundle.CATALOG_FORMAT


@pytest.mark.parametrize("recorded", [None, bundle.CATALOG_FORMAT + 1])
def test_stale_snapshot_is_rebuilt(github: FakeGitHub, cache: Path, recorded) -> None:
    folder = bundle.fetch("main", cache_dir=cache).path
    meta = json.loads((folder / "snapshot.json").read_text())
    meta.pop("catalog_format")
    if recorded is not None:
        meta["catalog_format"] = recorded
    (folder / "snapshot.json").write_text(json.dumps(meta))
    (folder / "leftover.txt").write_text("from the old snapshot")
    snap = bundle.fetch(SHA, cache_dir=cache)
    assert github.downloads() == 2
    assert snap.catalog_format == bundle.CATALOG_FORMAT and snap.path == folder
    assert not (folder / "leftover.txt").exists()
    assert sorted(p.name for p in cache.iterdir()) == [SHA]


def test_failed_rebuild_keeps_the_stale_snapshot(github: FakeGitHub, cache: Path) -> None:
    folder = bundle.fetch("main", cache_dir=cache).path
    meta = json.loads((folder / "snapshot.json").read_text())
    meta.pop("catalog_format")
    (folder / "snapshot.json").write_text(json.dumps(meta))
    github.archives.clear()
    with pytest.raises(bundle.FetchError, match="HTTP 404"):
        bundle.fetch(SHA, cache_dir=cache)
    assert (folder / "catalog.json").is_file()
    assert "catalog_format" not in json.loads((folder / "snapshot.json").read_text())
    assert sorted(p.name for p in cache.iterdir()) == [SHA]
