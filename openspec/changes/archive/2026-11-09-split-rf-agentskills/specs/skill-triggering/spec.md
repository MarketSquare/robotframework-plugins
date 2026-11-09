## ADDED Requirements

### Requirement: Sibling skills share a plugin

Skills that the "Sibling skills state their boundary" requirement pairs as siblings for the same task (rf-browser and rf-selenium; rf-requests and rf-restinstance) SHALL ship in the same plugin, so that a user who has one also has the boundary text of the other.

#### Scenario: Web siblings together
- **WHEN** the catalogue is listed
- **THEN** `rf-browser` and `rf-selenium` are both in `rf-web`, and `rf-requests` and `rf-restinstance` are both in `rf-api`

### Requirement: Trigger accuracy holds for partial installs

Trigger baselines SHALL be measured both with all plugins staged and with `rf-core` plus one technology plugin staged. With a partial install, the should-trigger queries of the staged skills SHALL meet the same thresholds as with all plugins. Queries for a technology whose plugin is not staged SHALL count as correct when no rf-* skill of another technology loads.

#### Scenario: Web only
- **WHEN** the trigger evaluation runs with `rf-core` and `rf-web` staged
- **THEN** the report shows recall for `rf-browser` and `rf-selenium` within the thresholds, and the rate at which an API or mobile query loaded a web skill
