# agent-plugin-marketplace Specification

## Purpose

Make this repository the `robotframework-plugins` marketplace from which Claude Code, GitHub Copilot (CLI and VS Code), Codex and Cursor install the programme's plugins, at user or project scope, at a released or pinned version.

## Requirements

### Requirement: One Claude-format marketplace serves every plugin-capable agent

The repository root SHALL carry `.claude-plugin/marketplace.json` with the name `robotframework-plugins` and the owner Robot Framework Foundation (MarketSquare). It SHALL list every plugin of the catalogue, with source `./plugins/<name>`, as `plugin-catalogue` defines; `rf-core` is the first. Each plugin directory SHALL carry `.claude-plugin/plugin.json`. The marketplace SHALL NOT list a bundle that copies other plugins.

These files SHALL be the only plugin manifests:
- The repository SHALL NOT add a root `plugin.json` in the Agent Plugins format, because Copilot CLI, Codex and Cursor prefer it over `.claude-plugin/plugin.json` and would then treat hooks and subagents as unsupported.
- It SHALL NOT add `.cursor-plugin/` manifests, because Cursor reads `.claude-plugin/` and converts Claude-format hooks itself.

A plugin that needs `rf-core` SHALL name it in `dependencies` without a version range, because every plugin is released at the same version from the same commit.

#### Scenario: Copilot CLI installs from the repository
- **WHEN** `copilot plugin marketplace add MarketSquare/robotframework-plugins` and `copilot plugin install rf-web@robotframework-plugins` run
- **THEN** `rf-web` and its dependency `rf-core` install, the subagents of `rf-core` are offered for delegation, and the hooks run on `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse` and `Stop`

#### Scenario: Codex installs from the repository
- **WHEN** `codex plugin marketplace add MarketSquare/robotframework-plugins` and `codex plugin add rf-core@robotframework-plugins` run, and the user trusts the plugin's hooks once
- **THEN** a session lists the `rf-core` skills under the plugin's namespace and the plugin hooks run

#### Scenario: VS Code loads the plugin
- **WHEN** VS Code Copilot loads `rf-core` through `chat.plugins.marketplaces` or `chat.pluginLocations`
- **THEN** agent mode lists its skills and subagents, and the plugin hooks run with `CLAUDE_PLUGIN_ROOT` set

#### Scenario: Manifests stay consistent
- **WHEN** CI validates the repository
- **THEN** each marketplace entry carries the same name as its plugin's `.claude-plugin/plugin.json`, the version is set only in `plugin.json` (no entry `version`, no `metadata.version`), no root `plugin.json` or `.cursor-plugin/` exists, and `claude plugin validate .` passes with no version-mismatch warning

#### Scenario: Claude Code installs from the new source
- **WHEN** `/plugin marketplace add MarketSquare/robotframework-plugins` and `/plugin install rf-api@robotframework-plugins` run in Claude Code
- **THEN** `rf-api` and `rf-core` install, and their skills are listed as `rf-api:<skill>` and `rf-core:<skill>`

### Requirement: The plugin sets no default main agent

The plugin SHALL NOT ship a `settings.json`, or a `settings` manifest key, that sets `agent`. Enabling the plugin SHALL leave the user's main agent unchanged, and the subagents SHALL be available only for delegation.

#### Scenario: Plugin without default agent
- **WHEN** the plugin tree is listed
- **THEN** it contains no `settings.json`, and `.claude-plugin/plugin.json` has no `settings.agent`

### Requirement: Install, scope and pinning are documented per agent

The README SHALL document, for Claude Code, Copilot CLI, VS Code Copilot, Codex and Cursor:
- how to add the marketplace and install `rf-core` and the technology plugins;
- what user scope and project scope mean for that agent, and the committed file that enables project scope where the agent supports one;
- how to pin a release, with a release tag (`#v<version>` or `--ref v<version>`) or `stable`, and that pinning the marketplace to a tag pins every plugin in it to that commit.

It SHALL state per agent:
- which plugin components work there (skills, subagents, hooks);
- any one-time step, such as trusting hooks in Codex (`/hooks`) or enabling VS Code's plugin and hook settings.

It SHALL point OpenCode, Goose and Claude Desktop users to the installer.

#### Scenario: Agent support matrix
- **WHEN** a reader looks up Codex in the README
- **THEN** it says that the plugin provides skills and hooks (after trusting them once with `/hooks`), that subagents come from the installer, and that project scope needs the per-user `codex plugin` commands

#### Scenario: Pinning example uses a plugin tag
- **WHEN** a reader looks up how to pin a release
- **THEN** the example uses a tag of the form `v<version>`, for example `v5.0.0`, and a note says that the older tags (`v1.1.0` to `v3.0.0` and `<plugin>--v1.0.0`) still install the releases they name but receive no updates

### Requirement: Releases keep the marketplace installable at a tag

Every release SHALL be tagged `v<version>` with the release version that `release-train` defines, on a commit whose every `.claude-plugin/plugin.json` carries `<version>`, so that a marketplace pinned to the tag installs exactly that release of every plugin. The tags from before this change (`v1.1.0` to `v3.0.0`, `rf-agentskills-v*`, `<plugin>--v*` and `robotframework-plugins-v*`) SHALL stay unchanged.

#### Scenario: Pinned install
- **WHEN** a user adds the marketplace pinned to `v5.0.0`
- **THEN** the installed `rf-core` and `rf-web` plugins both report version `5.0.0`

#### Scenario: Tag and manifest disagree
- **WHEN** the release workflow runs for a tag `v5.0.1` on a commit whose `plugins/rf-web/.claude-plugin/plugin.json` says `5.0.0`
- **THEN** the workflow fails before publishing anything and names both versions
