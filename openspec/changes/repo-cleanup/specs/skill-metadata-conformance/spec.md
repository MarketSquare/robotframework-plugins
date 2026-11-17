## MODIFIED Requirements

### Requirement: Repository references use the canonical identifiers

Subagent definitions, hook-injected context, eval task `skill:` fields, CI and release packaging, and user documentation SHALL refer to skills only by their `rf-<topic>` identifier or their `plugins/<plugin>/skills/rf-<topic>/` path. The legacy long directory names (`robotframework-*-skill`, `robotframework-results`, `robotframework-libdoc-*`) and the legacy short plugin names MUST NOT be used as skill identifiers.

#### Scenario: No legacy identifier remains
- **WHEN** the repository's skills, plugin agents and scripts, hooks, eval tasks, workflows, tests and README are searched for legacy skill identifiers
- **THEN** no match is found, apart from the changelogs and the installer's legacy-name list used for migration

#### Scenario: Release packages use the new directory names
- **WHEN** the release workflow builds a plugin's standalone skills tarball and its Claude Desktop skill archives
- **THEN** every packaged skill directory is named `rf-<topic>` and its name matches its `SKILL.md`
