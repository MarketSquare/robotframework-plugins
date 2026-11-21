## Why

rf-mcp (the Robot Framework MCP server) wants to stop shipping its own library skills and serve the official ones from this repository, by depending on the `robotframework-plugins` package ([issue #5](https://github.com/MarketSquare/robotframework-plugins/issues/5)). Everything it needs is already in the wheel, but only through the private `robotframework_plugins._assets` module, and `_assets/catalog.json` has no format version. A tool can't pin a version range against private names. And the package isn't on PyPI yet, so rf-mcp can't depend on it at all.

## What Changes

- **New public module `robotframework_plugins.bundle`**, listed in its `__all__`:
  - `CATALOG_FORMAT` (int, `1`), bumped only on a breaking change to the catalogue entries;
  - `catalog()`: the bundled plugins (active and deprecated), with name, version, status, tier, summary, libraries (`name`, `package`, `versions`), the `robotframework` range, `dependencies`, `bundle` and `bundled`;
  - `skills_dirs()`: `{plugin name: absolute Path of its skills/ folder}` for every active plugin with content, `rf-core` first, bundles left out. The paths stay valid for the life of the process.
- **An opt-in snapshot of the repository: `bundle.fetch(ref="stable")`.** It returns the same `catalog()` / `skills_dirs()` interface for a ref of this repository, so a tool can serve skills newer than its installed package:
  - `stable` (the released content) by default; `main`, another branch, a tag or a commit SHA when named explicitly;
  - the ref is resolved to a commit SHA, and the snapshot is downloaded once and cached by SHA, so repeat calls are offline and the tool can report which commit it serves;
  - the catalogue is built from the snapshot's `catalog.yaml` files with the same code as the wheel's, and a snapshot that fails that check, or whose archive has unsafe paths, is refused;
  - it only touches the network when called. Importing the module and the bundled API never do. On any failure it raises `bundle.FetchError`, and the caller keeps the bundled copy;
  - standard library only: no new dependencies.
- **`_assets/catalog.json` gets a top-level `"format": 1`** next to `"plugins"`, so tools that read the file directly can check it.
- **Catalogue entries gain `robotframework`** (the supported Robot Framework range from each `catalog.yaml`). The issue lists it as needed, and today the build hook drops it.
- **The installer README gets a "Python API" section** with the compatibility promise:
  - removing or renaming a public name, or removing a documented field, bumps `CATALOG_FORMAT` and is called out in the installer changelog;
  - new fields and new plugins aren't breaking changes;
  - the skill folder layout (`<skills dir>/<skill>/SKILL.md` plus `references/`) is part of the contract.
- **`_assets` stays the installer's internal module**; `bundle` wraps it, and the adapters keep using `_assets`.
- **The first PyPI release, `2026.11.0`, includes the API.** 2026.11.0 has no tag and isn't on PyPI yet, so the API goes into its changelog entry instead of a new version. The maintainer publishes it by pushing the `robotframework-plugins-v2026.11.0` tag; the release workflow uploads through trusted publishing after the maintainer approves the `pypi` environment.

The bundled copy stays the default and the fallback. Content from a branch is reviewed and has passed the PR checks, but it isn't released: plugin versions there can be unreleased, the full evals run later, and a revert can still land. Skills also ship scripts that agents run. So fetching is never automatic, and the README says what a consumer takes on by choosing `main`.

Out of scope: a reader for a project's install record (`bundle.installed_skills(project)`), which the issue leaves for a follow-up.

## Capabilities

### New Capabilities

- `installer-python-api`: the public `robotframework_plugins.bundle` module (catalogue, skill folders, format version, opt-in repository snapshots) and its compatibility promise.

### Modified Capabilities

None. The catalogue's new `format` key and `robotframework` field are additions that existing readers (`bundled_catalog()`, `catalog --json`) ignore or pass through.

## Impact

- **Code:**
  - `installer/src/robotframework_plugins/bundle.py` (new);
  - `installer/hatch_build.py` (writes `format` and `robotframework`, using catalogue code shared with `fetch()`);
  - `installer/src/robotframework_plugins/_catalog.py` (new: catalogue entries from plugin folders) and `_snapshot.py` (new: ref resolution, download, safe extraction, cache);
  - `installer/src/robotframework_plugins/_assets.py` (a helper that keeps a real path for the process lifetime, if needed).
- **Tests:** `tests/installer/` gets API tests, a wheel test (build the wheel, install it into a fresh venv, call the API) and snapshot tests against a local fake server (no real network in the test suite).
- **Docs:** `installer/README.md` ("Python API"), `installer/CHANGELOG.md` (2026.11.0, Added).
- **Release:** pushing the `robotframework-plugins-v2026.11.0` tag in November 2026 is the maintainer's step; this change only prepares it.
- **Network:** `fetch()` calls `api.github.com` (to resolve the ref) and `codeload.github.com` (the archive), unauthenticated, only when a consumer calls it. The installer CLI never calls it.
- **Consumers:** rf-mcp can declare `robotframework-plugins>=2026.11,<2027` and check `CATALOG_FORMAT` at runtime.
