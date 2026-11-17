## MODIFIED Requirements

### Requirement: PlatynUI library skill exists and follows the house structure

The repository SHALL provide a Robot Framework PlatynUI library skill at `plugins/rf-desktop/skills/rf-platynui/`, structured like the other library skills: a `SKILL.md` with valid frontmatter (`name: rf-platynui` matching its directory, and a `description`), a `references/` directory of deep-dive documents, and an `assets/examples/` directory of `.robot` examples.

#### Scenario: Skill directory and frontmatter
- **WHEN** the repository is inspected
- **THEN** `plugins/rf-desktop/skills/rf-platynui/SKILL.md` exists with frontmatter `name: rf-platynui` and a non-empty `description`
- **AND** `references/` and `assets/examples/` subdirectories exist with at least one file each

#### Scenario: Marketplace validation passes
- **WHEN** the marketplace/SKILL.md validation test suite runs
- **THEN** the skill passes the same frontmatter/structure checks applied to every other skill
