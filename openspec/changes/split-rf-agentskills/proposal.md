## Why

`rf-agentskills` ships everything in one plugin: Robot Framework itself, web, API, mobile and desktop. A web team loads Appium guidance it never uses, every new technology needs a PR against the same plugin, and the skill list grows into the agents' listing budgets (Claude Code shows about 8,000 characters of skill descriptions). The move to `MarketSquare/robotframework-plugins` already changes every install command, so splitting now costs users one break instead of two.

## What Changes

- **New `rf-core` plugin**: what every agent automating Robot Framework needs, whatever the system under test. Skills `rf-language`, `rf-setup` and `rf-python-library`; the subagents `rf-test-architect`, `rf-debug-expert` and `rf-migration-guide`; all hooks.
- **New technology plugins**, each depending on `rf-core`:
  - `rf-web`: `rf-browser`, `rf-selenium`;
  - `rf-api`: `rf-requests`, `rf-restinstance`;
  - `rf-mobile`: `rf-appium`;
  - `rf-desktop`: `rf-platynui`.
  Further technologies (database, Java, Windows-only tools) get a plugin when a maintainer group for them exists; they are not created empty.
- **BREAKING:** `rf-agentskills` becomes a bundle with no content of its own that installs all five plugins, at version 4.0.0. Skill names are unchanged, but their plugin prefix changes, for example from `rf-agentskills:rf-browser` to `rf-web:rf-browser`.
- **Library installs move to the library's own skill.** Each library skill owns its `uv add` command and post-install steps (for example `rfbrowser install`, Appium drivers). `rf-setup` keeps Python environments, uv, pip, Poetry, robotcode, Robocop and troubleshooting, plus a table of which plugin covers which library.
- **Library-to-library migration tables** (SeleniumLibrary to Browser, RequestsLibrary to RESTinstance) move from `rf-migration-guide` into the target library's skill as references.
- **Core never sends the agent to a skill that may not be installed.** The context-injection hook routes generically. Subagents and core skills that name a technology skill also name its plugin, and say to suggest installing it when it's missing. The `SessionStart` report names the plugin for each library it finds in the project environment.
- **Installer default selection.** `robotframework-plugins install` installs `rf-core` plus the technology plugins whose libraries the project declares. When it detects none, it installs every verified plugin, as today.
- **Evals cover partial installs**: a technology question with only `rf-core` installed must lead to a suggestion to install the right plugin, not to an answer from memory.
- **Spike first**: check whether Copilot CLI and Codex install plugin `dependencies`, and whether symlinked files survive a Windows checkout. The result picks how the bundle and shared files work on each agent.

## Capabilities

### New Capabilities
- `plugin-split`: the plugin set (`rf-core` and the technology plugins), what belongs in core, the `rf-agentskills` bundle, plugin dependencies, how core refers to skills in other plugins, the installer's default selection, and the upgrade path for existing users.

### Modified Capabilities
- `library-skill-install-guidance`: library skills own their install command and post-install steps; they point to `rf-setup` only for environments, other installers and troubleshooting.
- `setup-skill`: `rf-setup` drops the per-library post-install recipes and keeps a library-to-plugin table.
- `plugin-subagents`: library-specific routes name the plugin; library-to-library migration tables move to library skills.
- `rf-session-context-hooks`: injection routes generically and names only `rf-core` skills; the environment report names the plugin for each detected library.
- `skill-triggering`: boundaries between sibling skills in different plugins; trigger accuracy measured with partial installs.
- `skill-eval-harness`: a partial-install tier.

`installer-plugin-bootstrap` needs no delta here: `launch-plugin-programme` already writes one `enabledPlugins` entry per selected plugin, and migrated settings enable the `rf-agentskills` bundle, which still installs everything.

## Impact

- **Repository:** `plugins/rf-agentskills/` is split into five plugin directories plus the bundle. Each has its own `plugin.json`, `catalog.yaml`, CHANGELOG, tests, evals, variants, baseline and CODEOWNERS entry.
- **Users:** skill prefixes change. Project settings that enable `rf-agentskills@robotframework-plugins` keep everything through the bundle. Installer file-mode installs keep the same skill folders. Hook scripts move from the `rf-agentskills-files` folder to `rf-core-files`, and the upgrade cleans up the old location.
- **Sequencing:** applied inside `launch-plugin-programme`, after its task groups 1–3 and before its group 4. That change's first release (task 10.2) becomes the release of these plugins, so `rf-agentskills--v3.1.0` is never published.
- **Versions:** `rf-core`, `rf-web`, `rf-api`, `rf-mobile` and `rf-desktop` start at 1.0.0; the `rf-agentskills` bundle is 4.0.0.
