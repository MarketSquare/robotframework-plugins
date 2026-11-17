## MODIFIED Requirements

### Requirement: Skill exists with conformant frontmatter and layout

The repository SHALL provide the skill at `plugins/rf-core/skills/rf-language/` with:
- a `SKILL.md` whose frontmatter `name` is `rf-language` (equal to the directory name), with `description`, `license`, `compatibility` and `metadata` (`author`, `version`) in the form required for every shipped skill;
- a `references/` directory;
- an `assets/examples/` directory;
- a `scripts/` directory containing `rf_conventions.py`.

The `compatibility` text SHALL be at most 500 characters and SHALL state that Python and `robotframework>=7` in the project environment are needed for the bundled script, that the guidance is version-gated, and that `robotcode[all]>=2.8` is required in the project environment (it also provides Robocop). The skill SHALL contain only regular files (no symlinks).

#### Scenario: Directory and frontmatter
- **WHEN** `plugins/rf-core/skills/rf-language/SKILL.md` is parsed
- **THEN** `name` is `rf-language`, `license`, `compatibility` (≤ 500 characters) and `metadata` (`author`, `version`) are present, `scripts/rf_conventions.py` exists, and the skill validator used for all skills reports no violation

### Requirement: Skill is distributed to every channel without drift

The skill SHALL ship in the `rf-core` plugin, be copied unchanged into `bundles/rf-agentskills/` by the catalogue build (with its own `scripts/rf_conventions.py`), and be included in the installer assets. `scripts/build-catalog.py --check`, the drift check and the skill validator SHALL pass. In addition, the context-injection hook's skill list SHALL name `rf-language`; the subagents `rf-test-architect`, `rf-debug-expert` and `rf-migration-guide` SHALL direct the agent to `rf-language` (and, for migration, to its `references/migration.md` and the `rf_conventions` report); the `rf-core` README SHALL list the skill.

#### Scenario: Channels populated
- **WHEN** `scripts/build-catalog.py --check` runs
- **THEN** the bundle copy exists with `name: rf-language` and `scripts/check-drift.sh` exits 0

#### Scenario: Installer ships the skill
- **WHEN** the installer is built and installs for Claude Code into a temporary project
- **THEN** `.claude/skills/rf-language/SKILL.md` exists and is recorded in the install manifest

#### Scenario: Hook and subagents reference the skill
- **WHEN** a prompt mentioning a `.robot` or `.resource` file triggers the context-injection hook
- **THEN** the injected text lists `rf-language`
- **AND** `rf-test-architect.md`, `rf-debug-expert.md` and `rf-migration-guide.md` name `rf-language`
