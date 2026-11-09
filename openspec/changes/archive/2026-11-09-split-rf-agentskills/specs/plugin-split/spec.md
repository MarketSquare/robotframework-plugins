## Purpose

Defines how the Robot Framework content is split across plugins: what `rf-core` holds, which technology plugins exist, how they depend on each other, how the `rf-agentskills` bundle keeps existing installs whole, and how users get the right set without knowing the layout.

## ADDED Requirements

### Requirement: The content is split into a core and technology plugins

The catalogue SHALL contain these plugins, and every skill and subagent SHALL belong to exactly one of them:

| Plugin | Skills | Subagents | Hooks |
|---|---|---|---|
| `rf-core` | `rf-language`, `rf-setup`, `rf-python-library` | `rf-test-architect`, `rf-debug-expert`, `rf-migration-guide` | all |
| `rf-web` | `rf-browser`, `rf-selenium` | none | none |
| `rf-api` | `rf-requests`, `rf-restinstance` | none | none |
| `rf-mobile` | `rf-appium` | none | none |
| `rf-desktop` | `rf-platynui` | none | none |

A technology plugin SHALL NOT be added to the catalogue without content and at least one maintainer.

#### Scenario: Every skill has one home
- **WHEN** the skill directories of all plugins are listed
- **THEN** the nine skills appear once each, in the plugins the table names

#### Scenario: Empty plugin refused
- **WHEN** a PR adds `plugins/rf-database/` with a `catalog.yaml` but no skill, subagent or hook
- **THEN** the catalogue check fails and says a plugin needs content

### Requirement: Core holds only what every Robot Framework agent needs

`rf-core` SHALL hold content that applies whatever the system under test is: Robot Framework syntax and project structure, environment setup, Python keyword libraries and listeners, test design, debugging, version migration, and the validation and context hooks. Content that applies to one library or technology SHALL live in that technology's plugin. A hook in a technology plugin SHALL act only on that library's files, commands or output.

#### Scenario: Library-specific content outside core
- **WHEN** the files of `rf-core` are searched for keyword examples, locator strategies or install recipes of a specific library such as Browser, SeleniumLibrary, AppiumLibrary, RequestsLibrary, RESTinstance or PlatynUI
- **THEN** none is found, apart from the library-to-plugin table in `rf-setup` and library names used as detection signals

### Requirement: Technology plugins depend on core

Every technology plugin SHALL declare `rf-core` as a dependency in its `plugin.json`, with a version range of the core major version it is tested against. Installing a technology plugin SHALL therefore also install `rf-core` on agents that resolve plugin dependencies.

#### Scenario: Installing web brings core
- **WHEN** a Claude Code user runs `/plugin install rf-web@robotframework-plugins` with no plugin installed
- **THEN** `rf-web` and `rf-core` are both installed, and the `rf-browser`, `rf-selenium`, `rf-language`, `rf-setup` and `rf-python-library` skills are listed

### Requirement: The rf-agentskills bundle keeps existing installs whole

`rf-agentskills` SHALL remain in the catalogue as a bundle at version 4.0.0. Its `catalog.yaml` SHALL list `rf-core`, `rf-web`, `rf-api`, `rf-mobile` and `rf-desktop` under `bundle`, and it SHALL have no content of its own and no `dependencies`. The catalogue generator SHALL write a copy of those plugins' skills, subagents, hooks and hook scripts to `bundles/rf-agentskills/`, and the marketplace entry SHALL point there; the catalogue check SHALL fail when the copy is stale or holds a file the generator no longer writes. On every agent that installs plugins from the marketplace (Claude Code, Copilot CLI, VS Code Copilot, Codex), installing or updating `rf-agentskills` SHALL make the same nine skills, three subagents and hooks available as `rf-agentskills` 3.0.0 did, under the same `rf-agentskills:` prefix. Its changelog, its README and the release notes SHALL say that the skills of the separate plugins carry those plugins' prefixes, for example `rf-web:rf-browser`, and that installing the bundle and a technology plugin shows those skills twice.

#### Scenario: Existing project settings keep working
- **WHEN** a project's `.claude/settings.json` enables `rf-agentskills@robotframework-plugins`, a teammate has 3.0.0 installed, and updates after the split is released
- **THEN** the nine skills, three subagents and hooks are available under the `rf-agentskills` prefix, with no further step

#### Scenario: Bundle on Copilot CLI and Codex
- **WHEN** `rf-agentskills@robotframework-plugins` is installed in Copilot CLI and, separately, in Codex
- **THEN** each lists the nine skills, and the hooks run

#### Scenario: Stale bundle copy refused
- **WHEN** a PR edits `plugins/rf-web/skills/rf-browser/SKILL.md` without regenerating
- **THEN** the catalogue check fails and names `bundles/rf-agentskills/skills/rf-browser/SKILL.md`

### Requirement: Content names the plugin of a skill it does not ship

Text in a plugin that names a skill shipped by another plugin SHALL also name that plugin, for example "`rf-browser` (plugin `rf-web`)". A skill's frontmatter `description` is exempt, because the listing budget limits it and agents list each skill with its plugin prefix; so are changelogs, which record history. Where `rf-core` text routes work to a technology skill, it SHALL tell the agent to suggest installing the plugin when the skill is not available, instead of answering from memory.

#### Scenario: Lint finds an unqualified reference
- **WHEN** a file under `plugins/rf-core/` names `rf-appium` without naming `rf-mobile`
- **THEN** the cross-plugin reference lint fails and names the file and line

### Requirement: The installer picks plugins from the project

Without `--plugins`, and when the target has no earlier install, `robotframework-plugins install` SHALL install `rf-core` plus every verified technology plugin whose libraries the project declares. It SHALL read the declared dependencies from `pyproject.toml` (PEP 621, Poetry and dependency groups) and `requirements*.txt` in the project root, and match them against the library packages listed in each plugin's `catalog.yaml`. When it finds no such library, it SHALL install every verified plugin. It SHALL print which plugins it chose and why. The interactive wizard SHALL preselect the same plugins. `--plugins` SHALL override detection, and `--plugins all` SHALL select every verified plugin.

#### Scenario: Browser project
- **WHEN** the project's `pyproject.toml` depends on `robotframework-browser` and `robotframework-requests`, and `robotframework-plugins install --agent claude-code --yes` runs
- **THEN** `rf-core`, `rf-web` and `rf-api` are installed, `rf-mobile` and `rf-desktop` are not, and the output names the two packages that selected them

#### Scenario: Nothing detected
- **WHEN** the project declares no library that a plugin covers, and the same command runs
- **THEN** every verified plugin is installed, and the output says that no library was detected

### Requirement: Upgrades from rf-agentskills 3.x keep file-mode installs intact

An installer upgrade over a file-mode install made by `rf-agentskills` 0.8.0 or earlier SHALL, without `--plugins`, select every plugin that ships a skill the earlier install holds, so nothing the user had disappears. It SHALL also add the verified plugins for the libraries the project now declares, so the command the `SessionStart` report suggests adds a missing plugin without removing others. It SHALL leave the nine skill folders and three subagent files at their paths, record each file under the plugin that now ships it, move the hook and helper scripts from the `rf-agentskills-files` folder to the `rf-core-files` folder, rewrite the hook commands to the new paths, and remove the old folder. User-modified files SHALL be kept and reported, as for any upgrade.

#### Scenario: Claude Code file-mode upgrade
- **WHEN** a project with a file-mode install of all nine skills from `rf-agentskills` 0.8.0 runs `robotframework-plugins install --agent claude-code --yes`
- **THEN** all nine skill folders remain, the install record lists them under `rf-core`, `rf-web`, `rf-api`, `rf-mobile` and `rf-desktop`, `.claude/rf-core-files/` holds the hook scripts, `.claude/settings.json` hook commands point there, and `.claude/rf-agentskills-files/` is gone

#### Scenario: Narrowing is explicit
- **WHEN** the same project then runs `robotframework-plugins install --plugins rf-core,rf-web --agent claude-code --yes`
- **THEN** the API, mobile and desktop skills are removed, and the summary lists them
