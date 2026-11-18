## MODIFIED Requirements

### Requirement: Installer writes project-scope marketplace configuration

`robotframework-plugins install --mode plugin` (project scope) SHALL merge into the project's `.claude/settings.json` an `extraKnownMarketplaces` entry for `robotframework-plugins` (GitHub source `MarketSquare/robotframework-plugins`, optionally pinned to a tag with `--ref`) and one `enabledPlugins` entry `<plugin>@robotframework-plugins: true` for each selected plugin, keeping every other key. With `--agent copilot` it SHALL write the same keys to `.github/copilot/settings.json`. It SHALL copy no skills, subagents or hooks for these agents. The manifest SHALL record the merged keys so that uninstall removes only them. The committed entries SHALL be enough for Copilot CLI to load the plugins, and SHALL make VS Code recommend them and Claude Code enable them.

When the settings file holds the old `robotframework-agentskills` marketplace entry (GitHub source `manykarim/robotframework-agentskills`) and `rf-agentskills@robotframework-agentskills` in `enabledPlugins`, the installer SHALL replace them with the new marketplace entry and, without `--plugins`, enable `rf-core`, `rf-web`, `rf-api`, `rf-mobile` and `rf-desktop`, so that nothing the old plugin provided disappears. It SHALL keep any `--ref` pin the old entry carried unless a new `--ref` is given, and report the migration. An `rf-agentskills@robotframework-plugins` entry, from the bundle that is no longer listed, SHALL be replaced the same way.

#### Scenario: Copilot CLI picks up the committed configuration
- **WHEN** the committed `.claude/settings.json` holds the marketplace entry and an `enabledPlugins` entry and a teammate starts Copilot CLI in the trusted project
- **THEN** the plugin's skills, subagents and hooks are loaded without a user-level install

#### Scenario: Existing settings preserved
- **WHEN** `.claude/settings.json` already holds hooks and other plugins
- **THEN** after `--mode plugin` they are unchanged and the new entries are added; uninstall removes only those entries

#### Scenario: Old marketplace entry migrated
- **WHEN** `.claude/settings.json` holds `extraKnownMarketplaces.robotframework-agentskills` and `enabledPlugins["rf-agentskills@robotframework-agentskills"]`, and `robotframework-plugins install --mode plugin --agent claude-code --yes` runs
- **THEN** both old keys are gone, `extraKnownMarketplaces.robotframework-plugins` is present, `enabledPlugins` holds `rf-core`, `rf-web`, `rf-api`, `rf-mobile` and `rf-desktop` at `robotframework-plugins`, every other key is unchanged, and the output names the migration

#### Scenario: Bundle entry replaced
- **WHEN** `.claude/settings.json` enables `rf-agentskills@robotframework-plugins` and the same command runs
- **THEN** that key is gone and the five plugins are enabled instead
