## 1. Source and token (D1, D2)

- [x] 1.1 Add keyword-only `source` and `token` to `fetch()` in `_snapshot.py`.
  - Resolve them from the environment as in D2.
  - With a configured source, both requests go to that source.
  - The token is an unredirected header, sent only to the source's host.
  - `http://` with a token is refused for hosts other than the local machine.
  - Verify: the new tests in `tests/installer/test_bundle_fetch.py` for source, environment, token, redirect, `GITHUB_TOKEN` and plain HTTP pass.
- [x] 1.2 Keep every error free of the token. Verify: a test asserts the token string is absent from `FetchError` messages for a refused HTTP source and for an HTTP 401 from the source.

## 2. Catalogue format (D3)

- [x] 2.1 Write `catalog_format` and `built_by` into `snapshot.json`, add `Snapshot.catalog_format`, and treat a missing or other format as a cache miss. Verify: tests show a new snapshot has `catalog_format == bundle.CATALOG_FORMAT` and `built_by` naming the installed version.
- [x] 2.2 Swap a stale cached folder for a rebuilt one only once the rebuild is complete. Verify: tests show an old snapshot without a format is downloaded and rebuilt, and that a failed rebuild raises `FetchError` and leaves the old folder in place.

## 3. Missing stable (D4)

- [x] 3.1 Add the hint for a missing `stable` to the resolve error. Verify: a test calls `fetch()` against a fake GitHub without `stable` and checks the message names the first plugin release and `latest`.

## 4. Docs and changelog

- [x] 4.1 Update `installer/README.md`, "Python API":
  - the `fetch` row with `source` and `token`;
  - the source, token, proxy and `SSL_CERT_FILE`/`truststore` settings;
  - `Snapshot.catalog_format`;
  - the `stable` note.

  Verify: `python scripts/check-docs-voice.py` passes and the README names `ROBOTFRAMEWORK_PLUGINS_SOURCE`, `ROBOTFRAMEWORK_PLUGINS_TOKEN` and `catalog_format`.
- [x] 4.2 In `README.md`, say that `stable` appears with the first plugin release and to use `latest` until then. Add the additions to the unreleased 2026.11.0 entry of `installer/CHANGELOG.md` with links to #21, #22 and #23. Verify: both files mention it, and the AGENTS.md checks pass.

## 5. Checks and PR

- [x] 5.1 Run the installer and shared tests, ruff and the AGENTS.md checks. Verify: all pass locally. Done 2026-11-17: shared tests 906 passed (2 skipped), installer API tests 40 (15 new); ruff on the changed files, the eight AGENTS.md check scripts and `openspec validate --all --strict` pass.
- [ ] 5.2 Open a PR that closes #22 and #23 and references #21, and merge it with all checks green. Verify: the PR is merged and #22 and #23 are closed.
