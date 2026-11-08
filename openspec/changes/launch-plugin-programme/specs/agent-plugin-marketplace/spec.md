## MODIFIED Requirements

### Requirement: One Claude-format marketplace serves every plugin-capable agent

The repository root SHALL carry `.claude-plugin/marketplace.json` with the name `robotframework-plugins` and the owner Robot Framework Foundation (MarketSquare). It SHALL list every plugin of the catalogue, with source `./plugins/<name>`, as `plugin-catalogue` defines; `rf-agentskills` is the first. Each plugin directory SHALL carry `.claude-plugin/plugin.json`.

These files SHALL be the only plugin manifests:
- The repository SHALL NOT add a root `plugin.json` in the Agent Plugins format, because Copilot CLI, Codex and Cursor prefer it over `.claude-plugin/plugin.json` and would then treat hooks and subagents as unsupported.
- It SHALL NOT add `.cursor-plugin/` manifests, because Cursor reads `.claude-plugin/` and converts Claude-format hooks itself.

#### Scenario: Copilot CLI installs from the repository
- **WHEN** `copilot plugin marketplace add MarketSquare/robotframework-plugins` and `copilot plugin install rf-agentskills@robotframework-plugins` run
- **THEN** the plugin installs with its 9 skills, its 3 subagents are offered for delegation, and its hooks run on `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse` and `Stop`

#### Scenario: Codex installs from the repository
- **WHEN** `codex plugin marketplace add MarketSquare/robotframework-plugins` and `codex plugin add rf-agentskills@robotframework-plugins` run, and the user trusts the plugin's hooks once
- **THEN** a session lists the 9 skills under the plugin's namespace and the plugin hooks run

#### Scenario: VS Code loads the plugin
- **WHEN** VS Code Copilot loads the plugin through `chat.plugins.marketplaces` or `chat.pluginLocations`
- **THEN** agent mode lists the 9 skills and 3 subagents, and the plugin hooks run with `CLAUDE_PLUGIN_ROOT` set

#### Scenario: Manifests stay consistent
- **WHEN** CI validates the repository
- **THEN** each marketplace entry carries the same name as its plugin's `.claude-plugin/plugin.json`, the version is set only in `plugin.json` (no entry `version`, no `metadata.version`), no root `plugin.json` or `.cursor-plugin/` exists, and `claude plugin validate .` passes with no version-mismatch warning

#### Scenario: Claude Code installs from the new source
- **WHEN** `/plugin marketplace add MarketSquare/robotframework-plugins` and `/plugin install rf-agentskills@robotframework-plugins` run in Claude Code
- **THEN** the plugin installs and its skills are listed as `rf-agentskills:<skill>`

### Requirement: Install, scope and pinning are documented per agent

The README SHALL document, for Claude Code, Copilot CLI, VS Code Copilot, Codex and Cursor:
- how to add the marketplace and install a plugin;
- what user scope and project scope mean for that agent, and the committed file that enables project scope where the agent supports one;
- how to pin a released version, with a plugin release tag (`#<plugin>--v<version>` or `--ref <plugin>--v<version>`), and that pinning the marketplace to a tag pins every plugin in it to that commit.

It SHALL state per agent:
- which plugin components work there (skills, subagents, hooks);
- any one-time step, such as trusting hooks in Codex (`/hooks`) or enabling VS Code's plugin and hook settings.

It SHALL point OpenCode, Goose and Claude Desktop users to the installer.

#### Scenario: Agent support matrix
- **WHEN** a reader looks up Codex in the README
- **THEN** it says that the plugin provides skills and hooks (after trusting them once with `/hooks`), that subagents come from the installer, and that project scope needs the per-user `codex plugin` commands

#### Scenario: Pinning example uses a plugin tag
- **WHEN** a reader looks up how to pin a release
- **THEN** the example uses a tag of the form `rf-agentskills--v<version>`, and a note says the old `v<version>` tags still work for releases up to 3.0.0

### Requirement: Releases keep the marketplace installable at a tag

Every plugin release SHALL be tagged `<plugin>--v<version>`, on a commit whose `plugins/<plugin>/.claude-plugin/plugin.json` carries `<version>`, so that a marketplace pinned to the tag installs exactly that release of the plugin and a plugin dependency's version range can resolve against the tags. The tags `v1.1.0`, `v1.2.0` and `v3.0.0` from before the move SHALL stay unchanged; no new tag of the form `v<version>` SHALL be created.

#### Scenario: Pinned install
- **WHEN** a user adds the marketplace pinned to `rf-agentskills--v3.1.0`
- **THEN** the installed `rf-agentskills` plugin reports version `3.1.0`

#### Scenario: Tag and manifest disagree
- **WHEN** the release workflow runs for a tag `rf-agentskills--v3.2.0` on a commit whose `plugin.json` says `3.1.0`
- **THEN** the workflow fails before publishing anything and names both versions
