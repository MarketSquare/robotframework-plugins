"""Public Python API: robotframework_plugins.bundle (spec installer-python-api; public-bundle-api 3.1, 3.2)."""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import textwrap
import zipfile
from pathlib import Path

import pytest
from robotframework_plugins import _assets, bundle

ACTIVE_CONTENT = ("rf-core", "rf-api", "rf-desktop", "rf-mobile", "rf-web")


def test_public_names() -> None:
    assert set(bundle.__all__) == {"CATALOG_FORMAT", "catalog", "skills_dirs", "fetch", "Snapshot", "FetchError"}
    assert bundle.CATALOG_FORMAT == 1


def test_import_makes_no_network_call(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args, **kwargs):
        raise AssertionError(f"network call: {args[:2]!r}")

    for name in ("create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    code = "from robotframework_plugins import bundle; bundle.catalog(); bundle.skills_dirs()"
    # A fresh interpreter: the import itself must not connect either.
    guard = textwrap.dedent("""
        import socket
        def refuse(*a, **k): raise SystemExit("network call")
        socket.create_connection = socket.getaddrinfo = refuse
        socket.socket.connect = refuse
    """)
    subprocess.run([sys.executable, "-c", guard + code], check=True)
    assert bundle.catalog() and bundle.skills_dirs()


def test_library_matching_data() -> None:
    web = next(p for p in bundle.catalog() if p["name"] == "rf-web")
    browser = next(lib for lib in web["libraries"] if lib["name"] == "Browser")
    assert browser["package"] == "robotframework-browser" and browser["versions"]
    assert web["robotframework"].startswith(">=")
    for entry in bundle.catalog():
        assert {"name", "version", "status", "tier", "summary", "libraries", "robotframework",
                "dependencies", "bundle", "bundled"} <= set(entry), entry["name"]


def test_bundles_are_marked() -> None:
    agentskills = next(p for p in bundle.catalog() if p["name"] == "rf-agentskills")
    assert agentskills["bundle"] is True
    assert set(agentskills["bundled"]) == set(ACTIVE_CONTENT)


def test_caller_changes_dont_leak() -> None:
    first = bundle.catalog()
    first.pop()
    first[0]["name"] = "changed"
    second = bundle.catalog()
    assert len(second) == len(_assets.bundled_catalog())
    assert "changed" not in {p["name"] for p in second}


def test_skills_dirs_are_real_and_named_like_the_catalogue() -> None:
    dirs = bundle.skills_dirs()
    assert tuple(dirs) == ACTIVE_CONTENT
    for name, path in dirs.items():
        assert path.is_absolute() and path.is_dir(), name
        assert any(path.glob("*/SKILL.md")), name
    expected = [p["name"] for p in bundle.catalog() if p["status"] == "active" and not p["bundle"]]
    assert set(dirs) == set(expected)


def test_bundles_and_deprecated_plugins_left_out(two_plugin_bundle: Path) -> None:
    dirs = bundle.skills_dirs()
    assert "rf-example" in dirs
    assert "rf-old" not in dirs and "rf-agentskills" not in dirs
    assert next(iter(dirs)) == "rf-core"
    assert {p["name"] for p in bundle.catalog()} >= {"rf-old", "rf-agentskills"}


def test_file_and_constant_agree() -> None:
    doc = json.loads(_assets.bundle_root_traversable().joinpath("catalog.json").read_text(encoding="utf-8"))
    assert doc["format"] == bundle.CATALOG_FORMAT
    assert [p["name"] for p in doc["plugins"]] == [p["name"] for p in bundle.catalog()]


def test_no_catalogue_gives_empty_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "plugins" / "rf-core" / "skills" / "x").mkdir(parents=True)
    (tmp_path / "plugins" / "rf-core" / "skills" / "x" / "SKILL.md").write_text("x")
    monkeypatch.setattr(_assets, "bundle_root_traversable", lambda: tmp_path)
    assert bundle.catalog() == []
    assert bundle.skills_dirs() == {}


def test_skills_dirs_from_a_zip_import(tmp_path: Path) -> None:
    """Zip/frozen installs: the folders exist although the package lives in a zip."""
    pkg = Path(bundle.__file__).parent
    archive = tmp_path / "pkg.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        for f in pkg.rglob("*"):
            if f.is_file() and "__pycache__" not in f.parts:
                zf.write(f, Path("robotframework_plugins") / f.relative_to(pkg))
    script = textwrap.dedent(f"""
        import sys
        sys.path = [{str(archive)!r}] + [p for p in sys.path if "robotframework_plugins" not in p
                                         and "site-packages" not in p or p.endswith("site-packages")]
        import robotframework_plugins
        assert robotframework_plugins.__file__.startswith({str(archive)!r}), robotframework_plugins.__file__
        from robotframework_plugins import bundle
        dirs = bundle.skills_dirs()
        assert list(dirs) == {list(ACTIVE_CONTENT)!r}, list(dirs)
        for path in dirs.values():
            assert path.is_dir() and any(path.glob("*/SKILL.md")), path
        assert dirs == bundle.skills_dirs()  # one extraction, reused
        print("ok")
    """)
    out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "ok"


@pytest.mark.slow
def test_api_from_an_installed_wheel(tmp_path: Path) -> None:
    """The issue's acceptance test: build the wheel, install it into a fresh
    venv and use the API from there (public-bundle-api 5.1)."""
    import shutil

    if shutil.which("uv") is None:
        pytest.skip("uv not on PATH")
    repo = Path(__file__).resolve().parents[2]
    dist, venv = tmp_path / "dist", tmp_path / "venv"
    subprocess.run(["uv", "build", "--wheel", "-q", "-o", str(dist)], cwd=repo / "installer", check=True)
    (wheel,) = dist.glob("robotframework_plugins-*.whl")
    names = zipfile.ZipFile(wheel).namelist()
    assert "robotframework_plugins/py.typed" in names
    assert any(n.endswith(".dist-info/licenses/LICENSE") for n in names)
    assert "robotframework_plugins/bundle.py" in names
    assert json.loads(zipfile.ZipFile(wheel).read("robotframework_plugins/_assets/catalog.json"))["format"] == 1
    subprocess.run(["uv", "venv", "-q", "--python", sys.executable, str(venv)], check=True)
    python = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    subprocess.run(["uv", "pip", "install", "-q", "--python", str(python), str(wheel)], check=True)
    script = textwrap.dedent(f"""
        from robotframework_plugins import bundle
        assert bundle.CATALOG_FORMAT == 1 and callable(bundle.fetch)
        dirs = bundle.skills_dirs()
        # Other plugins (the template in CI, a community plugin) may be bundled too.
        assert list(dirs)[0] == "rf-core" and set(dirs) >= set({list(ACTIVE_CONTENT)!r}), list(dirs)
        for path in dirs.values():
            assert path.is_absolute() and path.is_dir() and any(path.glob("*/SKILL.md")), path
            assert "site-packages" in str(path), path
        active = [p["name"] for p in bundle.catalog() if p["status"] == "active" and not p["bundle"]]
        assert set(dirs) == set(active)
        print("ok")
    """)
    out = subprocess.run([str(python), "-I", "-c", script], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "ok"


def test_libraries_name_their_skills() -> None:
    """catalog-library-skills: ``libraries[].skills`` reaches tools unchanged (issue #7)."""
    by_name = {p["name"]: p for p in bundle.catalog()}
    web = {lib["name"]: lib for lib in by_name["rf-web"]["libraries"]}
    assert web["Browser"]["skills"] == ["rf-browser"]
    assert web["SeleniumLibrary"]["skills"] == ["rf-selenium"]
    api = {lib["name"]: lib["skills"] for lib in by_name["rf-api"]["libraries"]}
    assert api == {"RequestsLibrary": ["rf-requests"], "RESTinstance": ["rf-restinstance"]}
    for name, path in bundle.skills_dirs().items():
        for lib in by_name[name]["libraries"]:
            for skill in lib.get("skills", []):
                assert (path / skill / "SKILL.md").is_file(), (name, skill)
