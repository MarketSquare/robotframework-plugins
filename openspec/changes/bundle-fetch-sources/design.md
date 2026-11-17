## Context

`installer/src/robotframework_plugins/_snapshot.py` implements `fetch()` with the standard library only:
- **Resolve:** a non-SHA ref is resolved through `GET {GITHUB_API}/repos/{repo}/commits/{ref}`.
- **Download:** the archive comes from `GET {CODELOAD}/{repo}/tar.gz/{sha}`.
- **Check and cache:** the archive is checked, extracted into a temporary folder and moved into `<cache>/<sha>/` with `os.replace`. `snapshot.json` is written last and marks a finished snapshot.

The two base URLs are module constants that tests point at a fake GitHub on `127.0.0.1` (`tests/installer/test_bundle_fetch.py`). No request carries a token.

The capability spec `installer-python-api` comes from the open change `public-bundle-api` (tasks 7.2, 8.1 and 8.2 wait for its release). This change adds requirements beside it; see `specs/installer-python-api/spec.md`.

## Goals / Non-Goals

**Goals:**
- `fetch()` works through a GitHub-compatible mirror, with a token, without callers patching private constants.
- A token can't leak to a host it wasn't meant for.
- Old cached snapshots can't be served in a format the running wheel doesn't produce.

**Non-Goals:**
- Creating the `stable` branch. That is a release step for the maintainer (see Open Questions).
- Saving the API call for branches and tags by downloading `refs/heads/<branch>` archives directly (#22, point 2). A token raises the limit from 60 to 5,000 calls per hour, which covers the rf-mcp use (at most one fetch a day per machine). The direct download would also change how a ref is pinned before the download. It can come later without changing this API.
- Proxy support beyond what `urllib` already does (`HTTPS_PROXY`, `NO_PROXY`).

## Decisions

### D1. One `source` URL; the archive comes from the same API

With the default source, requests stay as today: `api.github.com` resolves the ref and `codeload.github.com` serves the archive, because the public download needs no API quota.

With a configured source, both requests go to that source:
- `GET {source}/repos/{repo}/commits/{ref}` to resolve the ref;
- `GET {source}/repos/{repo}/tarball/{sha}` to download it.

GitHub Enterprise (`https://<host>/api/v3`) and the GitHub remotes of Artifactory and Nexus serve both REST endpoints, so one URL configures everything.

Alternatives:
- A second setting for the archive host. Rejected: two settings that must match.
- Codeload-style paths on the mirror. Rejected: GitHub Enterprise has no codeload host under the API URL.

The tarball endpoint may redirect, for example to a storage host; `urllib` follows redirects. A trailing `/` on `source` is ignored. `REPOSITORY` stays fixed.

### D2. Token handling

**Where the token comes from**, in order:
1. the `token` argument;
2. `ROBOTFRAMEWORK_PLUGINS_TOKEN`;
3. `GITHUB_TOKEN`, but only when the source is the default github.com. A CI job's `GITHUB_TOKEN` is a GitHub credential and must not reach a third-party mirror.

**How it is sent:**
- The token is added with `Request.add_unredirected_header("Authorization", "Bearer …")`, so `urllib` doesn't copy it to a redirected request. The token reaches the source's host and no other.
- With the default source, the token goes only to `api.github.com`. The public codeload download stays anonymous.
- A token with an `http://` source is refused unless the host is `localhost`, `127.0.0.1` or `::1`, so the tests can use the fake server.

**Never exposed:** error messages use the host and HTTP status, never the request headers. The token is not written to `snapshot.json`.

Alternative: an empty-string token as "no token, even if the environment has one". Kept: `token=""` disables the environment lookup, which helps callers that manage credentials themselves.

### D3. Catalogue format and a rebuild that replaces a stale folder

`snapshot.json` gains:
- `catalog_format`: `_catalog.CATALOG_FORMAT`;
- `built_by`: `robotframework-plugins <__version__>`.

`Snapshot` gains `catalog_format: int | None = None`, read from `snapshot.json`.

`_cached()` returns a hit only when the recorded format equals the running `CATALOG_FORMAT`. On a miss over an existing folder, `_build()` works as before into a temporary folder. When that folder is complete, it is swapped in:
1. rename `<cache>/<sha>` to `<cache>/.stale-<sha>-<random>`;
2. `os.replace` the new folder into `<cache>/<sha>`;
3. delete the stale copy.

If step 2 fails because another process put a current snapshot there first, that snapshot is used, as today. If the build fails, the old folder was never touched, which matches the "Rebuild fails" scenario.

A full SHA with a stale cached snapshot needs the network for the rebuild. That is the price of never serving a wrong format, and it only happens once after a format change.

### D4. `stable` error message and docs

`_resolve()` adds a hint when the ref is `stable` and GitHub answers 404 or 422:

> ref 'stable' not found in MarketSquare/robotframework-plugins: it is created by the first plugin release; until then use 'latest' or a tag

The default stays `stable`. Option 1 of #21 (create `stable` now) is a release decision and left to the maintainer.

The installer README's `fetch` section and the repository README's marketplace sentence get the same note.

### D5. Tests extend the fake GitHub

The fake server:
- serves `/repos/{repo}/tarball/{sha}`;
- records each request's path and `Authorization` header;
- can answer with a redirect to a second fake server.

New tests:
- `source` passed as an argument and from the environment;
- the token sent to the source;
- no token after a redirect;
- `GITHUB_TOKEN` not sent to a mirror, but sent to the default API;
- `http://` with a token refused before any request;
- the token absent from errors;
- `catalog_format` and `built_by` written;
- a snapshot without a format, or with another one, rebuilt;
- a failed rebuild keeps the old folder;
- the `stable` hint.

None of them uses the real network.

## Risks / Trade-offs

- [A mirror serves the tarball endpoint under another path] → `source` is the API base URL, and GitHub-compatible remotes keep the REST paths. If one doesn't, the error names the URL and HTTP status, and the README says what the source must serve.
- [Renaming a cached folder fails on Windows while another process reads it] → the rename raises `OSError`, which becomes `FetchError`. The old snapshot stays usable for that process, and the next call tries again.
- [`token=""` versus no token] → documented in the README and the docstring.
- [Company CAs] → `urllib` uses Python's certificate store. The README points to `SSL_CERT_FILE`, and to `truststore` for using the system store.

## Migration Plan

Nothing to migrate: snapshots cached by 2026.11.0.dev1 have no `catalog_format`, and the next `fetch()` of their commit rebuilds them once. The changelog's unreleased 2026.11.0 entry lists the additions.

## Open Questions

- Should `stable` be created now, at the commit the 2026.11.0.dev1 wheel was built from (`f4e2a26`), as #21 suggests? Either answer leaves this change as it is; the maintainer decides and #21 stays open until then.
