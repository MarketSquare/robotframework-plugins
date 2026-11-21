## MODIFIED Requirements

### Requirement: The content is split into a core and technology plugins

The catalogue SHALL contain these plugins, and every skill and subagent SHALL belong to exactly one of them:

| Plugin | Skills | Subagents | Hooks |
|---|---|---|---|
| `rf-core` | `rf-language`, `rf-bdd`, `rf-setup`, `rf-python-library` | `rf-test-architect`, `rf-debug-expert`, `rf-migration-guide` | all |
| `rf-web` | `rf-browser`, `rf-selenium` | none | none |
| `rf-api` | `rf-requests`, `rf-restinstance` | none | none |
| `rf-mobile` | `rf-appium` | none | none |
| `rf-desktop` | `rf-platynui` | none | none |

A technology plugin SHALL NOT be added to the catalogue without content and at least one maintainer.

#### Scenario: Every skill has one home
- **WHEN** the skill directories of all plugins are listed
- **THEN** the ten skills appear once each, in the plugins the table names

#### Scenario: Empty plugin refused
- **WHEN** a PR adds `plugins/rf-database/` with a `catalog.yaml` but no skill, subagent or hook
- **THEN** the catalogue check fails and says a plugin needs content
