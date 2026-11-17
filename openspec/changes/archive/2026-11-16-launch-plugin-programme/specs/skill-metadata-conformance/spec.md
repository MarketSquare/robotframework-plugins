## MODIFIED Requirements

### Requirement: One identifier per skill across all channels

Each skill SHALL have exactly one identifier of the form `rf-<topic>`, unique across the catalogue. In `plugins/<plugin>/skills/`, the skill's directory name MUST equal the `name` field of its `SKILL.md` frontmatter, and every channel built from the plugin (installer assets, release tarballs, Desktop ZIPs) MUST use the same directory name.

#### Scenario: Directory equals name in every channel
- **WHEN** any `SKILL.md` under `plugins/*/skills/` or in a built channel is inspected
- **THEN** its frontmatter `name` equals the name of the directory that contains it

#### Scenario: Same identifier in every channel
- **WHEN** the skill directory names of a plugin and of a channel built from it are compared
- **THEN** the two sets are identical and every entry starts with `rf-`

#### Scenario: Plugin skill is namespaced by the plugin
- **WHEN** the Claude Code plugin is loaded
- **THEN** each skill is addressable as `<plugin>:<name>`, for example `rf-web:rf-browser` (or `rf-agentskills:rf-browser` through the bundle), where `<name>` is the same identifier used by the standalone channels

### Requirement: Skills declare runtime compatibility, license and metadata

Every skill SHALL declare `license: Apache-2.0`, a `compatibility` field that states the runtimes and packages it needs (Python floor, Robot Framework floor, library package and any external runtime such as Node.js, the Appium server, robotcode or uv), and `metadata` with at least `author` and `version`. `metadata.version` MUST equal the version in its plugin's `.claude-plugin/plugin.json`.

#### Scenario: Script-based skill states its Python dependencies
- **WHEN** the frontmatter of a skill that ships a Python script (for example `rf-language` or `rf-python-library`) is read
- **THEN** `compatibility` names the minimum Python version and `robotframework>=7`

#### Scenario: Library skill states its library and external runtime
- **WHEN** the frontmatter of `rf-appium` is read
- **THEN** `compatibility` names `robotframework-appiumlibrary` and the Appium server

#### Scenario: robotcode requirement stated
- **WHEN** the frontmatter of any shipped skill that runs a `robotcode` command is read
- **THEN** `compatibility` names `robotcode[all]>=2.8` in the project environment

#### Scenario: Version stays in step with the bundle
- **WHEN** `scripts/bump-version.sh rf-core minor` runs
- **THEN** the plugin's `plugin.json` and every one of its skills' `metadata.version` carry the new value, and the validator fails if any skill disagrees with its plugin

### Requirement: Skill validation runs in CI for all channels

The repository SHALL provide a skill validator that can run offline with no third-party dependencies and enforces the frontmatter and name/directory rules for every plugin's skills and the channels built from them. CI MUST run the validator on every push and pull request, and a violation MUST fail the build.

#### Scenario: CI fails on a mismatched directory
- **WHEN** a pull request adds `plugins/rf-web/skills/rf-foo/SKILL.md` with `name: rf-bar`
- **THEN** the CI skill-validation job fails and reports the mismatch

#### Scenario: Validator is exercised by tests
- **WHEN** the test suite runs
- **THEN** it includes cases that feed the validator a valid skill and invalid skills (bad charset, dir mismatch, long description, long compatibility, XML tag, unknown key) and asserts the expected outcome

## REMOVED Requirements

### Requirement: Sync propagates skills without renaming and removes stale copies

**Reason**: Root `skills/` and the sync step are removed; each plugin's `plugins/<name>/skills/` is the only source (`plugin-catalogue`, "Each plugin owns its sources, tests and evals").

**Migration**: Edit the skill under `plugins/<plugin>/skills/`. The drift check now covers only the generated Codex and OpenCode variants.
