## Context

See proposal.md (Why). The parts of the current package that shape the approach:

- `hatch_build.py` copies each active and deprecated plugin into `_assets/plugins/<name>/` and writes `_assets/catalog.json` as `{"plugins": [...]}`. Each entry is built from `catalog.yaml` and `plugin.json`: name, version, tier, status, summary, libraries, dependencies, bundle, bundled, plus replacement and deprecated_since when set. It drops `catalog.yaml`'s `robotframework` range.
- `_assets.py` reads the bundle with `importlib.resources.files`. `bundled_catalog()` returns the parsed list, `content_plugins()` the active non-bundle names with `rf-core` first, and `asset_root_path()` a real path through `as_file`, scoped to a `with` block.
- `as_file` returns the path itself for an unpacked install (wheel, editable). For a zip import it copies to a temporary location that is removed when the `with` block ends. On Python 3.10 and 3.11 it can't do this for directories: it calls `read_bytes()` on the directory. The package supports Python 3.10 and later.
- The wheel's `_assets/` is generated, so tests that check it either use the package as installed in the dev environment (editable, `_assets/` filled by the hook) or build a wheel (`test_wheel_contains_bundled_plugins`, marked slow).
- The repository has `main` and `latest` (both on the same commit today). RELEASING.md says the plugin release workflow moves `stable` and `latest`, but no plugin has been released yet, so `stable` doesn't exist.
- The installer's file-mode install makes no network call (`tests/installer/test_no_network.py`), and its README promises it sends nothing unless asked.
- `robotframework-plugins` 2026.11.0 has no tag and isn't on PyPI. The release workflow publishes on a `robotframework-plugins-v<version>` tag whose version must match `pyproject.toml` and the current month.

## Goals / Non-Goals

**Goals:**
- A public surface small enough to keep stable: one module, three names for the bundle and three for snapshots.
- Paths that consumers can hand to a directory-based skill provider and keep for the whole process.
- Tests that exercise the API as a consumer sees it: from an installed wheel, in a separate environment.

**Non-Goals:**
- Changing `_assets` or the adapters. `bundle` reads through `_assets`, and the adapters keep their own use of it.
- Making deprecated plugins' skills available through `skills_dirs()`: a consumer that wants them can read `catalog()`.
- A reader for a project's install record (issue #5, "Later").
- Type stubs or a typed `TypedDict` for entries: entries stay plain dicts, so new fields stay non-breaking.
- Fetching automatically, or as a fallback for the bundle: the bundle is always there, and a silent network call would break the no-network promise.
- Other repositories or forks as a `fetch()` source, authentication, and cache eviction. A consumer can delete the cache folder; the README says where it is.

## Decisions

### D1. `bundle` wraps `_assets`; entries are copies

`catalog()` returns `copy.deepcopy(_assets.bundled_catalog())`, so a caller can't change what the next call or the installer sees. `CATALOG_FORMAT = 1` is a module constant. The module has no import-time side effects (no extraction, no file reads), so `import robotframework_plugins.bundle` stays cheap for a server that only needs it on first use.

Alternative: move the reading code into `bundle` and make `_assets` call it. That is more churn for the adapters, and nothing in the API needs it.

### D2. `skills_dirs()` filters the catalogue itself

Keys are the catalogue entries with `status == "active"`, not a bundle (`is_bundle`), and with a `skills/` folder holding at least one `*/SKILL.md`, ordered with `rf-core` first, then catalogue order. This reuses the rule of `content_plugins()` but not the function itself: `content_plugins()` falls back to `("rf-core",)` when the catalogue is missing, which would invent an entry for a broken build. With no catalogue, `skills_dirs()` returns `{}` and `catalog()` returns `[]`.

### D3. Real paths for the life of the process

If the `_assets` Traversable is already a `pathlib.Path` (every normal or editable install), `skills_dirs()` returns `path / "plugins" / name / "skills"`, resolved. Otherwise (zip import, frozen app), the first call copies the whole `_assets` tree once into a `tempfile.mkdtemp()` directory by walking the Traversable (`iterdir`, `read_bytes`), and removes it with an `atexit` handler. Later calls reuse it. Walking the Traversable ourselves works on Python 3.10 and 3.11, where `as_file` can't copy directories.

Alternatives:
- `as_file` inside a module-level `ExitStack`: only works on 3.12+ for directories.
- Documenting "unpacked installs only": the issue asks for paths that stay valid, and frozen builds are a supported case in `_assets`' docstring.

### D4. One catalogue builder, used by the build hook and by `fetch()`

The entry-building code moves from `hatch_build.py` into a new private module `robotframework_plugins/_catalog.py` (`CATALOG_FORMAT`, `catalog_entries(plugins_dir)`, `has_content()`), using only the standard library and PyYAML (already a dependency). It adds `"robotframework": m.get("robotframework", "")` to each entry and raises a clear error for a missing manifest or required field. `hatch_build.py` loads that file by path (`importlib.util.spec_from_file_location`), because the package isn't importable at build time, and writes `{"format": CATALOG_FORMAT, "plugins": [...]}`. `bundle.CATALOG_FORMAT` re-exports the same constant, so the number lives in one place.

Existing readers use `.get("plugins")`, so the new key doesn't affect them, and the test fixtures that write a catalogue without `format` keep working.

Alternative: keep the builder in the hook and duplicate it in the snapshot code. Two copies of the rules would drift, and the spec requires that both build entries the same way.

### D5. Ship `py.typed`

Add the PEP 561 marker so a consumer's type checker sees the API's annotations (`list[dict[str, Any]]`, `dict[str, Path]`). It covers the whole package; `_assets` stays private by its name and the README, not by typing.

### D6. Tests: API, wheel in a fresh venv, zip import

- **Unit tests** against the dev install: names, entry fields, `rf-core` first, bundle and deprecated plugins left out (with the existing `two_plugin_bundle`-style fixtures for a deprecated entry), copies on each call, `format` in the file equals the constant.
- **Wheel test (slow):** `uv build --wheel`, `uv venv`, `uv pip install <wheel>`, then a short script in that venv that calls the API and checks the spec scenarios ("Real directories of the installed package", "Names match the catalogue"). This is the issue's acceptance test, and it catches a missing `py.typed`, `__all__` or `_assets` file in the wheel.
- **Zip test:** zip the installed package directory, import it from a fresh interpreter with only the zip on `sys.path`, and check that `skills_dirs()` paths exist and hold `SKILL.md`. That runs on whichever Python the CI matrix uses, including 3.10.

### D7. `fetch()`: resolve, download, check, cache

`_snapshot.py` does the work and `bundle.fetch()` wraps it. Standard library only (`urllib.request`, `tarfile`, `tempfile`, `os.replace`).

1. **Resolve.** A 40-hex `ref` is taken as the commit and looked up in the cache first, with no network call. Otherwise `GET https://api.github.com/repos/MarketSquare/robotframework-plugins/commits/<ref>` with `Accept: application/vnd.github.sha` returns the SHA as text. A 404 (for example `stable` before the first plugin release) becomes `FetchError: ref 'stable' not found`.
2. **Cache hit.** If `<cache>/<sha>/` holds a finished snapshot (a `snapshot.json` written last), return it.
3. **Download.** `GET https://codeload.github.com/MarketSquare/robotframework-plugins/tar.gz/<sha>` into a temporary file, with the `timeout` and a size cap (64 MB). `urllib` honours the usual proxy environment variables.
4. **Extract safely.** Only members under `<top>/plugins/` are extracted, by reading each member and writing it ourselves, not with `extractall`. A member that isn't a regular file or directory (symlink, hard link, device), or whose normalised path is absolute or has `..`, raises `FetchError` naming it. This works the same on Python 3.10 to 3.13, where `tarfile`'s `filter="data"` isn't available on every 3.10 or 3.11 patch release. Plugin `tests/` and `evals/` are skipped, as in the wheel.
5. **Check and build the catalogue** with `_catalog.catalog_entries()` on the extracted `plugins/`, and keep only `active` and `deprecated` plugins, as the wheel does.
6. **Commit to the cache.** Write `catalog.json` (with `format`) and `snapshot.json` (`ref`, `commit`, fetch time) into the temporary folder, then `os.replace` it to `<cache>/<sha>/`. If another process won the race, use its folder and drop ours.

A `Snapshot` holds the folder, `ref` and `commit`; its `catalog()` and `skills_dirs()` use the same filters as the bundled functions (D2), applied to the snapshot's catalogue. The default cache is `$XDG_CACHE_HOME` or `~/.cache` on Linux and macOS, and `%LOCALAPPDATA%` on Windows, each under `robotframework-plugins/snapshots/`.

Requests are unauthenticated. The API allows 60 per hour per IP, and only branch and tag refs use it, once per `fetch()` call; a consumer that calls `fetch()` once at start-up stays far below that.

Alternatives:
- `git clone --depth 1`: needs git on the machine and runs a program; the archive needs neither.
- Release archives from GitHub releases: only exist for tagged plugin releases, not for `main`.
- The raw files API, file by file: hundreds of requests per snapshot.

### D8. Tests for `fetch()` never use the real network

The test suite serves a fake GitHub on `127.0.0.1` (`http.server` in a thread) with one endpoint per step, and points `_snapshot`'s two base URLs at it. Archives are built in the test from a small plugin tree, so the tests cover a good snapshot, a cache hit, a SHA served offline (with sockets blocked as in `test_no_network.py`), a 404 ref, a timeout, a `../` member, a symlink member, and a `catalog.yaml` without `status`. One extra test, marked `network` and skipped by default, fetches `main` from GitHub for a manual check before a release.

### D9. Release as 2026.11.0

The API goes into the unreleased 2026.11.0 changelog entry under "Added". Publishing is the maintainer's step: push the `robotframework-plugins-v2026.11.0` tag in November 2026 and approve the `pypi` environment. If the tag is pushed in December or later, the release workflow's month check requires `2026.12.0`, and the changelog heading moves with it.

## Risks / Trade-offs

- [The promise freezes field names the installer also uses internally] → Only the fields listed in the spec are promised; the installer can add fields freely, and a breaking rename bumps `CATALOG_FORMAT`.
- [Extracted copies in zip mode cost disk and a startup delay] → Only in zip/frozen mode, once per process, and the bundle is a few MB.
- [A consumer pins `<2027` but the calendar version moves every month] → `CATALOG_FORMAT` is the compatibility signal, not the version; the README says so.
- [`main` content is merged but not released: versions can be unreleased, the full evals run later, a revert can land, and skills ship scripts that agents run] → `fetch()` is opt-in and defaults to `stable`; the README states what choosing `main` means; snapshots are pinned to a SHA, so a consumer can report and reproduce what it served.
- [`stable` doesn't exist until the first plugin release] → `fetch()` raises a clear `FetchError` for it, and the README says to use `main` until then.
- [GitHub rate limits or outages] → Commit-SHA refs are served from the cache without the network; any failure is a `FetchError` and the bundle stays usable.
- [Publishing depends on the maintainer and the trusted-publishing setup on pypi.org] → The tasks end with the maintainer's release steps, and the PR description lists them.

## Migration Plan

No migration: the API is new and the catalogue changes are additions. Rollback is a revert before the release. After the release, removing the API would itself be a breaking change under the promise.
