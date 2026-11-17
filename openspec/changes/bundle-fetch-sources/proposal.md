## Why

`bundle.fetch()` (added for #5) is about to be used by rf-mcp to serve the official skills from a ref, and three open issues block that use:

- **#21:** the default ref `stable` doesn't exist yet, so `fetch()` without a ref fails with `ref 'stable' not found`, and the message doesn't say what to use instead.
- **#22:** `fetch()` only talks to `api.github.com` and `codeload.github.com` and sends no token. That fails in company networks that reach GitHub through GitHub Enterprise or an artifact manager. Behind a shared IP, the 60 unauthenticated API calls per hour run out.
- **#23:** a cached snapshot doesn't record the catalogue format it was built with. A later wheel with another format can be handed an old snapshot without knowing it.

## What Changes

- **Source and token for `fetch()`** (#22):
  - `fetch(ref, *, source=None, token=None, cache_dir=None, timeout=30)`.
  - `source` is the base URL of a GitHub-compatible API (GitHub Enterprise, an Artifactory or Nexus GitHub remote). It defaults to `ROBOTFRAMEWORK_PLUGINS_SOURCE`, then `https://api.github.com`.
  - `token` defaults to `ROBOTFRAMEWORK_PLUGINS_TOKEN`; `GITHUB_TOKEN` is used only with the default github.com source, so a GitHub credential never goes to a mirror.
  - The token goes only to the configured host and is not passed on through redirects. It is never sent over plain HTTP, except to the local machine.
  - The README documents the settings, the proxy variables `urllib` already honours, and `SSL_CERT_FILE` for company CAs.
- **Snapshots record their catalogue format** (#23):
  - `snapshot.json` gets `catalog_format` and `built_by`, and `Snapshot.catalog_format` exposes the format. It is `None` for snapshots from before this change.
  - `fetch()` rebuilds a cached snapshot whose format differs from the running wheel's `CATALOG_FORMAT`, or is missing.
- **A missing `stable` names the way out** (#21):
  - `fetch()` keeps `stable` as its default, because rf-mcp will recommend that channel.
  - When `stable` doesn't exist, the `FetchError` says it appears with the first plugin release and names `latest` or a tag.
  - The installer README and the repository README say the same, including for a marketplace pin.
  - Creating the `stable` branch before a release is the maintainer's decision and is not part of this change.

No breaking change: every new argument is keyword-only with the old behaviour as its default.

## Capabilities

### New Capabilities

- `installer-python-api`: requirements for snapshot sources and tokens, the snapshot's catalogue format, and the message for a missing `stable`. The capability is introduced by the open change `public-bundle-api`, which isn't archived yet. This change only adds new requirements, so the two changes archive in either order.

### Modified Capabilities

(none)

## Impact

- `installer/src/robotframework_plugins/_snapshot.py`: source and token handling, `snapshot.json` fields, the format check on a cache hit, a rebuild that replaces a stale folder, the error for `stable`.
- `installer/src/robotframework_plugins/bundle.py`: unchanged exports; `fetch` and `Snapshot` come from `_snapshot`.
- `tests/installer/test_bundle_fetch.py`: the fake GitHub gains the tarball endpoint, header recording and a redirect to a second server.
- `installer/README.md`, `README.md`, `installer/CHANGELOG.md` (the unreleased 2026.11.0 entry).
- No new dependencies: standard library only, as before. No Robot Framework capability is involved, so no robotcode command applies.
