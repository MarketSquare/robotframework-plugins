## ADDED Requirements

### Requirement: Partial-install tier

The task bank SHALL contain, for each technology plugin, at least one task that runs with only `rf-core` staged and asks for work in that plugin's technology. The task SHALL pass when the agent names the right plugin to install, or produces code that passes the task's gating check, and SHALL fail when the agent writes library-specific code that fails the check. The tier SHALL run on the same models and replicates as the narrow tier.

#### Scenario: Browser task with core only
- **WHEN** the partial-install task "add a login test using Browser Library" runs with only `rf-core` staged
- **THEN** the run passes if the answer names `rf-web` for installation, or if the produced suite passes the Browser gating check, and the result is reported separately from the full-install runs

#### Scenario: Every technology plugin covered
- **WHEN** the coverage check runs
- **THEN** it fails and names any technology plugin without a partial-install task
