## MODIFIED Requirements

### Requirement: Setup skill exists and follows the house structure

The repository SHALL provide a skill at `plugins/rf-core/skills/rf-setup/` with a `SKILL.md` whose frontmatter has `name: rf-setup` (matching its directory) and a non-empty `description`, a `references/` directory and an `assets/examples/` directory.

#### Scenario: Skill directory and frontmatter
- **WHEN** the repository is inspected
- **THEN** `plugins/rf-core/skills/rf-setup/SKILL.md` exists with frontmatter `name: rf-setup` and a description that mentions installing Robot Framework and uv, venv/pip and poetry
- **AND** `references/` and `assets/examples/` exist and each contain at least one file

#### Scenario: Marketplace validation passes
- **WHEN** the marketplace/SKILL.md validation test suite runs
- **THEN** the skill passes the same frontmatter and structure checks applied to every other skill
