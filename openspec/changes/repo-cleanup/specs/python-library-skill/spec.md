## MODIFIED Requirements

### Requirement: Python library skill exists and follows the house structure

The repository SHALL provide a skill at `plugins/rf-core/skills/rf-python-library/` with a `SKILL.md` whose frontmatter has `name: rf-python-library`, a `description`, a `compatibility` field that names Python ≥ 3.10 and `robotframework>=7`, a `references/` directory, a `scripts/` directory and an `assets/examples/` directory. `SKILL.md` SHALL be at most 300 lines and SHALL contain, in this order, the sections: a quick reference with version gate, a default library template, decision tables, placement and import, agent workflow, Gotchas, when to read the references, and Companion Skills.

#### Scenario: Directory, frontmatter and size
- **WHEN** the repository is inspected
- **THEN** `plugins/rf-core/skills/rf-python-library/SKILL.md` exists with `name: rf-python-library`, a non-empty `description` and a `compatibility` value that mentions Python and `robotframework>=7`
- **AND** the file has at most 300 lines and all required sections in the stated order

#### Scenario: Spec validator passes
- **WHEN** the skill metadata validator and the marketplace validation tests run
- **THEN** the new skill passes the same checks as every other shipped skill

### Requirement: Distributed without drift

The skill SHALL ship in the `rf-core` plugin, be copied unchanged into `bundles/rf-agentskills/` by the catalogue build, be included in the installer assets, be named in the `UserPromptSubmit` hook's skill list, and be listed in the `rf-core` README. `scripts/build-catalog.py --check` and `scripts/check-drift.sh` SHALL pass, and the script SHALL be a regular file (no symlink) in every channel.

#### Scenario: All channels in sync
- **WHEN** `scripts/build-catalog.py --check` and then `scripts/check-drift.sh` run
- **THEN** both pass, and the plugin and the bundle each contain `rf-python-library/scripts/check_library.py` as a regular file

#### Scenario: Hook mentions the skill
- **WHEN** the context-injection hook runs on the prompt "my robot framework library says it contains no keywords"
- **THEN** the injected text names `rf-python-library`
