## Purpose

The `robotframework-plugins` package gives other tools a stable, public Python API to the plugin content it bundles: the catalogue and each plugin's skill folder, with a format version they can pin against.

## ADDED Requirements

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

#### Scenario: Bundles are marked
- **WHEN** a tool reads the `rf-agentskills` entry
- **THEN** its `bundle` is true and `bundled` names the plugins it bundles

#### Scenario: Caller changes don't leak
- **WHEN** a tool removes an entry from the list `catalog()` returned and calls `catalog()` again
- **THEN** the second list still has every bundled plugin

### Requirement: Skill folders of bundled plugins

`skills_dirs()` SHALL return a mapping from plugin name to the absolute path of that plugin's `skills/` folder, for every `active` plugin that is not a bundle and has a `skills/` folder, with `rf-core` first and the others in catalogue order. Each path SHALL be an existing directory for the life of the process, also when the package is imported from a zip archive. Each folder SHALL hold one sub-folder per skill with a `SKILL.md`, following the Agent Skills format.

#### Scenario: Real directories of the installed package
- **WHEN** a tool calls `skills_dirs()` in an environment where the built wheel is installed
- **THEN** every value is an absolute, existing directory, and each holds at least one `*/SKILL.md`

#### Scenario: Names match the catalogue
- **WHEN** a tool compares `skills_dirs()` with `catalog()`
- **THEN** its keys are exactly the names of the active, non-bundle catalogue entries that have skills, with `rf-core` first

#### Scenario: Bundles and deprecated plugins left out
- **WHEN** the catalogue holds the `rf-agentskills` bundle or a deprecated plugin
- **THEN** neither is a key of `skills_dirs()`

### Requirement: Catalogue format version

The bundled catalogue file SHALL carry a top-level `"format"` key with the same value as `CATALOG_FORMAT`, next to `"plugins"`. `CATALOG_FORMAT` SHALL change only on a breaking change to the catalogue: removing or renaming a field listed in "Catalogue of bundled plugins", or changing its meaning. Adding fields or plugins SHALL NOT change it.

#### Scenario: File and constant agree
- **WHEN** a tool reads `_assets/catalog.json` from the installed package
- **THEN** its `format` equals `bundle.CATALOG_FORMAT`

### Requirement: Documented compatibility promise

The installer README SHALL have a "Python API" section that names the public module and its public names, gives a short usage example, and states the compatibility promise: what bumps `CATALOG_FORMAT`, what doesn't, that the skill folder layout is part of the contract, and that breaking changes are named in the installer changelog. The private `_assets` module SHALL be documented there as not part of the API. The section SHALL also say that `fetch()` uses the network, that the bundled copy is the default, and that content from a branch other than `stable` is merged but not released.

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
