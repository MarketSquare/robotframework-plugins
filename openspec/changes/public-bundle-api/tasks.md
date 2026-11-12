## 1. Branch

- [x] 1.1 Branch `change/public-bundle-api` from `main` and commit this change's artifacts there; verify `git log origin/main..HEAD` shows only this change.

## 2. Shared catalogue builder (D4)

- [x] 2.1 Move the entry-building code from `installer/hatch_build.py` into `installer/src/robotframework_plugins/_catalog.py` (`CATALOG_FORMAT`, `catalog_entries()`, `has_content()`), add `robotframework` to each entry and a clear error for a missing manifest or required field; have the hook load it by path and write `{"format": CATALOG_FORMAT, "plugins": [...]}`. Verify a rebuilt `_assets/catalog.json` (`uv build --wheel`, or reinstalling `installer` editable) has `format: 1` and `rf-web`'s `robotframework` is `>=7.0`, and that `uv build --sdist` followed by a wheel build from the sdist still works.
- [x] 2.2 Check that existing readers still work; verify `uv run pytest tests/installer` passes, including fixtures that write a catalogue without `format`.

## 3. Bundled API (D1, D2, D3, D5)

- [x] 3.1 Add `installer/src/robotframework_plugins/bundle.py` with `CATALOG_FORMAT` (from `_catalog`), `catalog()`, `skills_dirs()` and `__all__`, wrapping `_assets`; add `py.typed`. Verify unit tests in `tests/installer/test_bundle_api.py` for "Public names", "Import makes no network call", "Library matching data", "Bundles are marked", "Caller changes don't leak", "Names match the catalogue", "Bundles and deprecated plugins left out" (a fixture bundle with a deprecated plugin) and "File and constant agree", plus an empty result for a bundle without a catalogue.
- [x] 3.2 Implement the zip/frozen path of `skills_dirs()` (one extraction per process, removed at exit); verify a test that zips the installed package, imports it in a fresh interpreter with only the zip on `sys.path`, and finds existing `SKILL.md` files under every returned path.

## 4. Repository snapshots (D7, D8)

- [x] 4.1 Add `installer/src/robotframework_plugins/_snapshot.py` (resolve, cache lookup, download with timeout and size cap, safe extraction of `plugins/`, catalogue check with `_catalog`, atomic move into the cache) and `bundle.fetch()`, `bundle.Snapshot` and `bundle.FetchError`. Verify tests in `tests/installer/test_bundle_fetch.py` against a fake GitHub on `127.0.0.1` for "Snapshot of main", "Same interface as the bundle", "Second fetch reuses the cache", "Commit SHA offline" (sockets blocked), "Network down", "Unsafe archive refused" (a `../` member and a symlink member), "Broken plugin manifest refused", a 404 ref (`stable` not found) and a timeout.
- [x] 4.2 Check that the installer never fetches; verify `tests/installer/test_no_network.py` still passes and a test asserts that no CLI module imports `_snapshot`.
- [x] 4.3 Add a test marked `network`, skipped by default, that fetches `main` from GitHub and checks the scenario "Snapshot of main"; verify it passes when run with `-m network` locally.

## 5. Wheel test (D6)

- [x] 5.1 Add a slow test that builds the wheel, installs it into a fresh `uv venv`, and runs a script there checking "Real directories of the installed package" and "Names match the catalogue", that `bundle.fetch` is importable, that `py.typed` is in the wheel, and that `catalog.json` has `format: 1`; verify it passes locally and in the CI job that runs the slow installer tests (or add it to one). Local: passes. CI: the Test job didn't have uv, so the existing wheel test skipped there; this change adds `astral-sh/setup-uv` to it. CI on #6: passes on Windows with Python 3.10 (with `test_wheel_contains_bundled_plugins` and the zip test, which ran in CI for the first time).

## 6. Docs and changelog

- [x] 6.1 Add a "Python API" section to `installer/README.md`: the public names, a short example (library matching, skill folders, `fetch("main")` with the bundle as fallback), the compatibility promise from the spec, that `_assets` is private, that `fetch()` is the only API that uses the network, where the cache lives, and that content from a branch other than `stable` is merged but not released (and `stable` only exists after the first plugin release). Verify `scripts/check-docs-voice.py` passes.
- [x] 6.2 Add the API, `fetch()`, the `format` key and the `robotframework` field to the 2026.11.0 entry of `installer/CHANGELOG.md` under "Added"; verify `scripts/check-docs-voice.py` passes.

## 7. Checks and PR

- [x] 7.1 Run `uv run pytest tests/installer` (with the slow tests), `ruff check installer`, `scripts/check-drift.sh` and `scripts/build-catalog.py --check`; verify all pass. Done: `tests` (819 passed), `tests/installer` with slow tests (274 passed), the new tests on Python 3.10, drift, catalogue and docs voice pass. `ruff check installer` reports 58 findings in files this change doesn't touch (CI doesn't lint the installer); the new and changed files are clean.
- [ ] 7.2 Open a PR against `main` that closes #5 (ask before posting); verify the required checks pass. Opened as #6: all checks pass except `required-reviews` (needs a review or the admin bypass).

## 8. Release (maintainer)

- [ ] 8.1 After the merge, the maintainer pushes the `robotframework-plugins-v2026.11.0` tag in November 2026 (or bumps to `2026.12.0` first, if later) and approves the `pypi` environment; verify `pip install robotframework-plugins==2026.11.0` in a fresh venv, then `python -c "from robotframework_plugins import bundle; print(bundle.CATALOG_FORMAT, list(bundle.skills_dirs()), bundle.fetch('main').commit)"`.
- [ ] 8.2 Comment on #5 with the released version and the API names (ask before posting); verify the comment is on the issue.
