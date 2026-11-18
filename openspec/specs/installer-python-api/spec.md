# installer-python-api Specification

## Purpose
The public Python API of the `robotframework-plugins` package (`robotframework_plugins.bundle`), which other tools such as rf-mcp use to serve the bundled plugins or a snapshot of a repository ref.

## Requirements

### Requirement: Snapshot source is configurable

`fetch()` SHALL take a keyword-only `source`: the base URL of a GitHub-compatible REST API that serves the repository (for example GitHub Enterprise or an artifact manager's GitHub remote). Without `source`, `fetch()` SHALL use the `ROBOTFRAMEWORK_PLUGINS_SOURCE` environment variable, and without that, github.com. With a configured source, every request of the fetch, both resolving the ref and downloading the archive, SHALL go to that source. A cached snapshot SHALL be served whichever source is configured, because it is keyed by commit.

#### Scenario: Mirror passed as an argument
- **WHEN** a tool calls `fetch("main", source="https://ghe.example.com/api/v3")`
- **THEN** the ref is resolved and the archive downloaded through `https://ghe.example.com/api/v3`, and no request goes to github.com

#### Scenario: Mirror from the environment
- **WHEN** `ROBOTFRAMEWORK_PLUGINS_SOURCE` is set and a tool calls `fetch("main")` without `source`
- **THEN** the requests go to that source

### Requirement: Snapshot token is sent only to its source

`fetch()` SHALL take a keyword-only `token`. Without it, `fetch()` SHALL use `ROBOTFRAMEWORK_PLUGINS_TOKEN`, and only when the source is github.com, `GITHUB_TOKEN`. A token SHALL be sent as `Authorization: Bearer <token>` only on requests to the source's own address; it SHALL NOT be sent to another host, including a host the source redirects to. `fetch()` SHALL refuse with `FetchError`, before any request, to send a token over plain HTTP to a host other than the local machine. No message, error or file written by `fetch()` SHALL contain the token.

#### Scenario: Token reaches the source
- **WHEN** a tool calls `fetch("main", source=<mirror>, token="t0k")`
- **THEN** the mirror receives `Authorization: Bearer t0k` on its requests

#### Scenario: Redirect doesn't carry the token
- **WHEN** the source answers the archive request with a redirect to another host
- **THEN** the request to that other host has no `Authorization` header

#### Scenario: GitHub token stays with GitHub
- **WHEN** `GITHUB_TOKEN` is set, `ROBOTFRAMEWORK_PLUGINS_TOKEN` is not, and a tool calls `fetch("main", source=<mirror>)`
- **THEN** the mirror receives no `Authorization` header

#### Scenario: Plain HTTP refused for a token
- **WHEN** a tool calls `fetch("main", source="http://mirror.example.com", token="t0k")`
- **THEN** it raises `FetchError` without sending any request, and the message doesn't contain the token

### Requirement: Snapshots record their catalogue format

A snapshot written by `fetch()` SHALL record in its metadata the catalogue format it was built with (the building package's `CATALOG_FORMAT`) and the package name and version that built it. `Snapshot.catalog_format` SHALL give the recorded format, or `None` for a snapshot that has none. When the cache holds a snapshot of the commit whose recorded format differs from the running package's `CATALOG_FORMAT`, or is missing, `fetch()` SHALL treat it as a cache miss and build the snapshot again, replacing the old one only when the new one is complete. A caller SHALL never receive a snapshot whose format differs from the running package's `CATALOG_FORMAT`.

#### Scenario: Format in a new snapshot
- **WHEN** a tool calls `fetch("main")` and the snapshot is built
- **THEN** `Snapshot.catalog_format` equals `bundle.CATALOG_FORMAT`, and the snapshot's metadata names `robotframework-plugins` and the installed version

#### Scenario: Old snapshot rebuilt
- **WHEN** the cache holds a snapshot of the commit without a recorded format, and a tool calls `fetch(<that SHA>)`
- **THEN** the archive is downloaded again, and the returned snapshot has `catalog_format` equal to `bundle.CATALOG_FORMAT`

#### Scenario: Rebuild fails
- **WHEN** a stale snapshot of the commit is cached and the download for the rebuild fails
- **THEN** `fetch()` raises `FetchError`, and the stale snapshot is neither returned nor removed

### Requirement: A missing stable ref names the alternatives

`fetch()` SHALL keep `stable` as its default ref. When `stable` is not found in the repository, the `FetchError` SHALL say that `stable` is missing and name a release tag (`v<version>`), or `main` for unreleased changes, as the refs to use instead; there is no `latest` branch any more. The installer README and the repository README SHALL say that every release moves `stable`.

#### Scenario: Default ref before the first release
- **WHEN** the repository has no `stable` ref and a tool calls `fetch()`
- **THEN** it raises `FetchError` whose message names `stable`, a release tag and `main`, and not `latest`

### Requirement: Catalogue entries keep their keys without bundles

`bundle.catalog()` and `Snapshot.catalog()` entries SHALL keep the `bundle` and `bundled` keys, with the values `false` and `[]`, so that `bundle.CATALOG_FORMAT` stays `1` and tools that read the keys keep working. The keys SHALL be dropped only together with a change of `CATALOG_FORMAT`.

#### Scenario: Keys present and constant
- **WHEN** `bundle.catalog()` is called on a release without bundles
- **THEN** every entry has `bundle` equal to `false` and `bundled` equal to `[]`, and `bundle.CATALOG_FORMAT` is `1`
