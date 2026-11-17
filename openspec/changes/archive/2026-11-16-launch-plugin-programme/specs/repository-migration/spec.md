## Purpose

Defines how `robotframework-agentskills` moves into `MarketSquare/robotframework-plugins` without losing history, which names change and which stay, and how the old repository and PyPI package are wound down without breaking existing users.

## ADDED Requirements

### Requirement: History and tags move with the code

The repository SHALL contain the complete commit history of `manykarim/robotframework-agentskills` `main`, joined to the repository's initial commit by a merge, so that `git log` and `git blame` reach the original commits. Every content tag (`v*`) and installer tag (`rf-agentskills-v*`) SHALL be copied and SHALL point to the same commits as in the old repository.

#### Scenario: Blame reaches original commits
- **WHEN** `git log --follow plugins/rf-agentskills/skills/rf-browser/SKILL.md` runs in the new repository
- **THEN** it lists the commits made in the old repository, with their original authors and dates

#### Scenario: Old tags resolve
- **WHEN** `git rev-parse v1.2.0^{commit}` runs in both repositories
- **THEN** both return the same commit id

#### Scenario: Initial commit is kept
- **WHEN** the history of `main` is listed
- **THEN** it contains the repository's initial commit and a merge that joins it to the copied history

### Requirement: Rename map

The programme SHALL apply exactly this rename. Anything not listed keeps its name.

| Old | New |
|---|---|
| Marketplace name `robotframework-agentskills` | `robotframework-plugins` |
| GitHub source `manykarim/robotframework-agentskills` | `MarketSquare/robotframework-plugins` |
| Marketplace owner `manykarim` | `Robot Framework Foundation` (MarketSquare) |
| PyPI package `rf-agentskills` | `robotframework-plugins` |
| CLI command `rf-agentskills` | `robotframework-plugins` |
| Python module `rf_agentskills` | `robotframework_plugins` |

The plugin `rf-agentskills`, its skill names, its subagent names, the `rf-skill-eval` harness and the per-skill folder names SHALL keep their names.

#### Scenario: No stale repository references
- **WHEN** tracked files outside `openspec/changes/archive/`, `CHANGELOG.md` files and dated reports are searched for `manykarim/robotframework-agentskills` and for the marketplace name `robotframework-agentskills`
- **THEN** the only matches are the documented migration notes

#### Scenario: Skill invocation names unchanged
- **WHEN** the plugin is installed from the new marketplace
- **THEN** its skills are listed as `rf-agentskills:rf-browser` and so on, exactly as before

### Requirement: The old repository points to the new home

Before it is archived, the old repository SHALL get a final commit whose README starts with a notice naming the new repository, the new marketplace commands and the new PyPI package. The old repository SHALL then be archived (read-only), not deleted, so that existing marketplace sources and pinned tags keep resolving.

#### Scenario: Existing pinned install still works
- **WHEN** a user who added `manykarim/robotframework-agentskills` pinned to `v3.0.0` reinstalls after the old repository is archived
- **THEN** the install succeeds with version 3.0.0

#### Scenario: Visitors find the new home
- **WHEN** a visitor opens the old repository's README
- **THEN** the first section names `MarketSquare/robotframework-plugins` and the commands to switch

### Requirement: The old PyPI package forwards to the new one

The final `rf-agentskills` release on PyPI, `0.9.0`, SHALL depend on `robotframework-plugins` at or above its first calendar-version release, SHALL provide an `rf-agentskills` command that prints a one-line deprecation notice to stderr and then runs `robotframework-plugins` with the same arguments and exit code, and SHALL say in its PyPI description that the project has moved. No later `rf-agentskills` release SHALL be made.

#### Scenario: Old command keeps working
- **WHEN** a user runs `uvx rf-agentskills install --agent claude-code --yes`
- **THEN** stderr shows the deprecation notice naming `robotframework-plugins`, and the install completes as it would with `uvx robotframework-plugins install --agent claude-code --yes`
