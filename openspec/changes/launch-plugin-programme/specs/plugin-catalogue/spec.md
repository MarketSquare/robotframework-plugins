## Purpose

Defines the programme manifest every plugin carries, the catalogue generated from those manifests, and how users find and install a chosen set of plugins from the one `robotframework-plugins` marketplace on every supported agent.

## ADDED Requirements

### Requirement: Every plugin carries a programme manifest

Every directory `plugins/<name>/` SHALL contain `catalog.yaml` with these fields:
- `name`: equal to the directory name and to the plugin manifest name;
- `summary`: one sentence, at most 160 characters;
- `tier`: `verified` or `community`;
- `status`: `active`, `deprecated` or `removed`;
- `maintainers`: one or more entries, each with a GitHub handle;
- `libraries`: the Robot Framework libraries the plugin covers, each with its PyPI package name and a supported version range;
- `robotframework`: the supported Robot Framework version range;
- `agents`: the agents the plugin is tested with;
- `replacement` and `deprecated_since`: required when `status` is `deprecated`.

CI SHALL validate every `catalog.yaml` against a published JSON Schema and SHALL fail on a missing or invalid manifest.

#### Scenario: Missing manifest fails CI
- **WHEN** a PR adds `plugins/new-plugin/` without `catalog.yaml`
- **THEN** the catalogue check fails and names the missing file

#### Scenario: Deprecated plugin without replacement fails CI
- **WHEN** a manifest sets `status: deprecated` and omits `replacement`
- **THEN** schema validation fails on that field

### Requirement: The catalogue is generated, not hand-written

The README catalogue table and `docs/catalog.md` SHALL be generated from the `catalog.yaml` files, listing every plugin with status `active` or `deprecated`: name, version (from its `plugin.json`), summary, tier, status, libraries and maintainers. CI SHALL fail when the committed catalogue differs from the generated one.

#### Scenario: Stale catalogue fails CI
- **WHEN** a PR changes a plugin's `summary` without regenerating the catalogue
- **THEN** the catalogue check fails and prints the command that regenerates it

### Requirement: The marketplace lists every active and deprecated plugin

`.claude-plugin/marketplace.json` SHALL be generated from the `catalog.yaml` files and the plugin manifests. It SHALL list exactly the plugins whose status is `active` or `deprecated`, each with `source` `./plugins/<name>`, no `version` (the version comes from the plugin's `plugin.json`), and `tags` that include the plugin's tier (`verified` or `community`) and, when deprecated, `deprecated`.

Removing or renaming a plugin SHALL add an entry to the top-level `renames` map: `"<name>": null` for a removed plugin and `"<old>": "<new>"` for a renamed one. Existing `renames` entries SHALL NOT be changed or deleted. `marketplace.json` SHALL set `forceRemoveDeletedPlugins` to `true`.

#### Scenario: Removed plugin leaves the marketplace
- **WHEN** a manifest's status changes to `removed`
- **THEN** CI fails until the plugin's marketplace entry is removed and `renames` maps its name to `null`

#### Scenario: Renames history is append-only
- **WHEN** a PR deletes or edits an existing `renames` entry
- **THEN** the catalogue check fails and names the entry

#### Scenario: Tier visible in the marketplace
- **WHEN** a user browses the marketplace in Claude Code
- **THEN** each plugin's tags show `verified` or `community`

### Requirement: The installer installs a chosen set of plugins

`robotframework-plugins install` SHALL accept `--plugins <name>[,<name>...]`. Without `--plugins`, it SHALL install every `active` plugin with tier `verified`. It SHALL refuse a `removed` or unknown name with an error that lists the available plugins, and SHALL warn, naming the replacement, when a selected plugin is `deprecated`. In the interactive wizard, plugin selection SHALL be a step showing each plugin's tier and status.

#### Scenario: Default install
- **WHEN** `robotframework-plugins install --agent claude-code --yes` runs and the catalogue holds one verified and one community plugin
- **THEN** only the verified plugin is installed

#### Scenario: Unknown plugin
- **WHEN** `robotframework-plugins install --plugins rf-nope --agent claude-code --yes` runs
- **THEN** it exits non-zero, writes nothing, and lists the available plugin names

### Requirement: Users can browse the catalogue from the installer

`robotframework-plugins catalog` SHALL print the installer's own version and every `active` and `deprecated` plugin bundled in the installed package with its name, version, tier, status and summary. `robotframework-plugins catalog --json` SHALL print the same data as JSON.

#### Scenario: Catalogue as JSON
- **WHEN** `robotframework-plugins catalog --json` runs
- **THEN** the output parses as JSON and contains the installer version and one entry per bundled active or deprecated plugin, with `name`, `version`, `tier`, `status` and `summary`

### Requirement: Each plugin owns its sources, tests and evals

Each plugin's content SHALL have one source, `plugins/<name>/`: its skills, subagents, hooks, scripts and generated variants. Tests of a plugin's content SHALL live in `plugins/<name>/tests/`, and its `rf-skill-eval` tasks and baselines in `plugins/<name>/evals/`. The repository root SHALL NOT hold a second copy of any plugin's skills, and no step SHALL sync skills from the root into a plugin. Root `eval/`, `tests/` and `scripts/` SHALL hold only the shared harness, repository-wide checks and tooling. In other specs, a skill path `skills/<skill>/` means `plugins/<plugin>/skills/<skill>/`.

On a PR, CI SHALL run the shared tests and the tests and evals of every plugin the PR changes, and the tests of the plugins those depend on or that depend on them (`rf-core`'s tests check the routes to technology skills). On `main` and in the nightly job, CI SHALL run all of them.

#### Scenario: No root skills copy
- **WHEN** the repository tree is listed
- **THEN** there is no root `skills/` directory and no `scripts/sync-skills.sh`

#### Scenario: PR runs only the changed plugin's tests
- **WHEN** a PR changes only files under `plugins/rf-mobile/`
- **THEN** CI runs the shared tests and the tests of `rf-mobile` and of `rf-core`, which it depends on, and not the tests of `rf-web`

### Requirement: Names are unique across the catalogue

Every skill name and every subagent name SHALL be unique across all `active` and `deprecated` plugins, and so SHALL every path the installer writes a plugin's hook scripts to. The catalogue check SHALL fail on a duplicate and name both plugins.

#### Scenario: Duplicate skill name
- **WHEN** a PR adds `plugins/rf-web-extra/skills/rf-browser/` while `rf-web` ships `rf-browser`
- **THEN** the catalogue check fails and names `rf-browser`, `rf-web` and `rf-web-extra`

### Requirement: Shared files have one owner

A file used by more than one plugin SHALL live in one plugin. Every other plugin that needs it SHALL carry a copy that `scripts/build-catalog.py` generates and its `--check` keeps in step, as it does for the `rf-agentskills` bundle. A plugin SHALL NOT contain a symlink, because Codex drops symlinks when it installs a plugin (split-rf-agentskills design D5); the catalogue check SHALL fail on one and name it. The security gate SHALL treat a change to a shared file as a change to every plugin that carries a copy.

#### Scenario: Symlink in a plugin
- **WHEN** a plugin contains a symlink, whether it points inside or outside the repository
- **THEN** the catalogue check fails and names the link

#### Scenario: Shared hook change scans both plugins
- **WHEN** a PR changes a hook script that a second plugin carries a copy of
- **THEN** the security gate scans both plugins

### Requirement: Each installer release states what it bundles

The release notes of every installer release, the README and `docs/catalog.md` SHALL include a generated table of the plugin versions the installer bundles, headed by the installer version.

#### Scenario: Release notes carry the table
- **WHEN** an installer release is published
- **THEN** its notes contain a table with one row per bundled plugin, giving its name, version and tier
