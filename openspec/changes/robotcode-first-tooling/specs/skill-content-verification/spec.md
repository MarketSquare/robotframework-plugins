## MODIFIED Requirements

### Requirement: Deterministic keyword checker gates CI

The repository SHALL provide a deterministic checker that extracts the Robot Framework content of library skills, analyses it with `robotcode analyze code` against the skill's target library, the standard libraries and the user keywords defined in the same skill, and reports keyword calls that are unknown, deprecated or called with the wrong number of arguments. Legacy `Run Keyword If`/`Unless` calls SHALL be reported from Robocop's deprecation rule. It SHALL exit non-zero when any call is unknown, deprecated, has an argument error or is a legacy `Run Keyword If`/`Unless`, unless an allowlist entry covers the call. Each allowlist entry SHALL name the skill, the file, the keyword and a reason. Findings SHALL name the Markdown or example file and line the call comes from, not a generated file. The checker SHALL run in a CI job and in the pytest suite. When a target library cannot be imported, the checker SHALL report that skill as skipped and SHALL NOT pass it silently.

#### Scenario: Clean repository passes
- **WHEN** the checker runs on the repository with all target libraries installed
- **THEN** it exits 0 and reports each checked skill with its file count

#### Scenario: Injected defect fails
- **WHEN** a fixture skill contains a call to a deprecated or nonexistent keyword that no allowlist entry covers
- **THEN** the checker exits non-zero and names the skill, file, line and keyword, with close-match suggestions when available

#### Scenario: Wrong argument count fails
- **WHEN** a fixture skill calls `Convert To Upper Case` with three arguments
- **THEN** the checker exits non-zero and names the skill, file, line and keyword with RobotCode's argument message

#### Scenario: Allowlisted exception passes
- **WHEN** a call is unknown but matches an allowlist entry for that skill and file
- **THEN** the checker does not fail on it

#### Scenario: Stale allowlist entry reported
- **WHEN** an allowlist entry matches no call in the current content
- **THEN** the checker fails and names the stale entry

#### Scenario: Missing library is not a silent pass
- **WHEN** a target library cannot be imported
- **THEN** the checker's output marks that skill as `skipped (library not installed)`
- **AND** in CI, where all target libraries are installed, a skipped skill fails the job
