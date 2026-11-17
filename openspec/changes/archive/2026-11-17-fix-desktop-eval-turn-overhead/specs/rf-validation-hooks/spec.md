## MODIFIED Requirements

### Requirement: Formatting drift check

The plugin SHALL provide a non-blocking formatting check for written `.robot`/`.resource` files using Robocop's formatter in check mode (`robocop format --check`), surfacing the proposed diff as a suggestion without failing the operation. The check SHALL be off by default and SHALL run only when `RF_AGENTSKILLS_FORMAT_CHECK` is truthy, because a formatting suggestion leads the agent to reformat and re-check a file that is otherwise correct.

#### Scenario: Formatting suggestion is surfaced
- **WHEN** `RF_AGENTSKILLS_FORMAT_CHECK` is truthy and a `.robot` file is written with inconsistent formatting (e.g. 2-space separators or trailing whitespace)
- **THEN** the hook surfaces the formatter's proposed changes as informational output
- **AND** the formatting difference alone does NOT cause a model-facing error (exit `2`)

#### Scenario: Disabled by default
- **WHEN** `RF_AGENTSKILLS_FORMAT_CHECK` is not set and a `.robot` file with inconsistent formatting is written
- **THEN** the hook output contains no formatting suggestion, and no formatter process is started
