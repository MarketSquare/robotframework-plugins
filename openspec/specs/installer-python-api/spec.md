# installer-python-api Specification

## Purpose
The public Python API of the `robotframework-plugins` package (`robotframework_plugins.bundle`), which other tools such as rf-mcp use to serve the bundled plugins or a snapshot of a repository ref.

## Requirements

### Requirement: Public bundle module

The package SHALL provide a public module `robotframework_plugins.bundle` whose `__all__` lists `CATALOG_FORMAT`, `catalog`, `skills_dirs`, `fetch`, `Snapshot` and `FetchError`. Importing it SHALL NOT require network access or any dependency beyond the package's own, and SHALL NOT write to the user's home or project folders.

#### Scenario: Public names
- **WHEN** a tool runs `from robotframework_plugins import bundle`
- **THEN** `bundle.__all__` contains `CATALOG_FORMAT`, `catalog`, `skills_dirs`, `fetch`, `Snapshot` and `FetchError`, and `bundle.CATALOG_FORMAT == 1`

#### Scenario: Import makes no network call
- **WHEN** a tool imports `robotframework_plugins.bundle` and calls `catalog()` and `skills_dirs()` with every network connection refused
- **THEN** both return the bundled content and no connection is attempted

### Requirement: Catalogue of bundled plugins

`catalog()` SHALL return one entry per bundled plugin (status `active` or `deprecated`), in the order of the bundled catalogue. Each entry SHALL have at least `name`, `version`, `status`, `tier`, `summary`, `libraries` (a list of `{name, package, versions}`), `robotframework` (the supported Robot Framework version range), `dependencies`, `bundle` and `bundled`. It SHALL return a new list on each call, so a caller changing it doesn't change later results.

#### Scenario: Library matching data
- **WHEN** a tool reads the `rf-web` entry of `catalog()`
- **THEN** its `libraries` contains `{"name": "Browser", "package": "robotframework-browser", "versions": ...}`, and its `robotframework` is a version range such as `>=7.0`

#### Scenario: Caller changes don't leak
- **WHEN** a tool removes an entry from the list `catalog()` returned and calls `catalog()` again
- **THEN** the second list still has every bundled plugin

### Requirement: Skill folders of bundled plugins

`skills_dirs()` SHALL return a mapping from plugin name to the absolute path of that plugin's `skills/` folder, for every `active` plugin that has a `skills/` folder, with `rf-core` first and the others in catalogue order. Each path SHALL be an existing directory for the life of the process, also when the package is imported from a zip archive. Each folder SHALL hold one sub-folder per skill with a `SKILL.md`, following the Agent Skills format.

#### Scenario: Real directories of the installed package
- **WHEN** a tool calls `skills_dirs()` in an environment where the built wheel is installed
- **THEN** every value is an absolute, existing directory, and each holds at least one `*/SKILL.md`

#### Scenario: Names match the catalogue
- **WHEN** a tool compares `skills_dirs()` with `catalog()`
- **THEN** its keys are exactly the names of the active catalogue entries that have skills, with `rf-core` first

#### Scenario: Deprecated plugins left out
- **WHEN** the catalogue holds a deprecated plugin
- **THEN** it is not a key of `skills_dirs()`

### Requirement: Catalogue format version

The bundled catalogue file SHALL carry a top-level `"format"` key with the same value as `CATALOG_FORMAT`, next to `"plugins"`. `CATALOG_FORMAT` SHALL change only on a breaking change to the catalogue: removing or renaming a field listed in "Catalogue of bundled plugins", or changing its meaning. Adding fields or plugins SHALL NOT change it.

#### Scenario: File and constant agree
- **WHEN** a tool reads `_assets/catalog.json` from the installed package
- **THEN** its `format` equals `bundle.CATALOG_FORMAT`

### Requirement: Documented compatibility promise

The installer README SHALL have a "Python API" section that names the public module and its public names, gives a short usage example, and states the compatibility promise: what bumps `CATALOG_FORMAT`, what doesn't, that the skill folder layout is part of the contract, and that breaking changes are named in `CHANGELOG.md`. The private `_assets` module SHALL be documented there as not part of the API. The section SHALL also say that `fetch()` uses the network, that the bundled copy is the default, and that content from a branch other than `stable` is merged but not released.

#### Scenario: Promise in the README
- **WHEN** a tool author reads the installer README
- **THEN** it explains `catalog()`, `skills_dirs()` and `CATALOG_FORMAT`, and when `CATALOG_FORMAT` changes

### Requirement: Opt-in snapshot of a repository ref

`fetch(ref="stable", *, cache_dir=None, timeout=30)` SHALL return a `Snapshot` of the plugins at a ref of the `MarketSquare/robotframework-plugins` repository. `ref` SHALL accept a branch, a tag or a full commit SHA, with `stable` as the default. A `Snapshot` SHALL have `ref`, `commit` (the full commit SHA it was built from), `catalog()` and `skills_dirs()`, which follow the requirements "Catalogue of bundled plugins" and "Skill folders of bundled plugins" for the plugins at that commit (status taken from each plugin's `catalog.yaml`). The network SHALL be used only inside `fetch()`; the installer's own commands SHALL NOT call it.

#### Scenario: Snapshot of main
- **WHEN** a tool calls `fetch("main")`
- **THEN** it gets a `Snapshot` whose `commit` is the SHA `main` pointed to, and whose `skills_dirs()` lists the active content plugins of that commit, with existing `*/SKILL.md` files

#### Scenario: Same interface as the bundle
- **WHEN** a tool compares a snapshot's `catalog()` entries with `bundle.catalog()`'s
- **THEN** they have the same fields, built by the same rules

### Requirement: Snapshots are pinned and cached

`fetch()` SHALL resolve `ref` to a commit SHA before downloading, and store each snapshot under a cache folder keyed by that SHA (default: the user's cache directory, `robotframework-plugins/snapshots/`; `cache_dir` overrides it). A snapshot already in the cache SHALL be reused without downloading again; a full commit SHA as `ref` SHALL be served from the cache without any network call. A snapshot SHALL be written to the cache only when complete, so an interrupted fetch leaves no partial snapshot behind.

#### Scenario: Second fetch reuses the cache
- **WHEN** a tool calls `fetch("main")` twice while `main` hasn't moved
- **THEN** the archive is downloaded once, and both snapshots have the same `commit` and the same paths

#### Scenario: Commit SHA offline
- **WHEN** a snapshot for a commit is cached and a tool calls `fetch(<that SHA>)` with every network connection refused
- **THEN** it returns that snapshot

### Requirement: Snapshots are checked and failures are explicit

`fetch()` SHALL raise `FetchError`, with a message naming the cause, and leave the cache unchanged when the ref can't be resolved, the download fails or times out, the archive holds an entry that is not a regular file or directory or whose path would leave the snapshot folder, or a plugin's `catalog.yaml` or `plugin.json` is missing or lacks a field the catalogue requires. A `FetchError` SHALL NOT affect the bundled `catalog()` and `skills_dirs()`. `fetch()` SHALL NOT run any code from the snapshot.

#### Scenario: Network down
- **WHEN** a tool calls `fetch("main")` with every network connection refused and nothing cached for it
- **THEN** it raises `FetchError`, and `bundle.skills_dirs()` still returns the bundled folders

#### Scenario: Unsafe archive refused
- **WHEN** the downloaded archive holds an entry `../outside.txt` or a symbolic link
- **THEN** `fetch()` raises `FetchError` naming the entry, and nothing is written outside a temporary folder or into the cache

#### Scenario: Broken plugin manifest refused
- **WHEN** a plugin in the snapshot has a `catalog.yaml` without `status`
- **THEN** `fetch()` raises `FetchError` naming the plugin and the field

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
