## MODIFIED Requirements

### Requirement: Opt-in per-file dry run

When `RF_AGENTSKILLS_FILE_DRYRUN` is truthy, per-file validation of a `.robot` suite file (not `.resource`, not `__init__.robot`) SHALL additionally run `robotcode robot --dryrun` on that file from the project root, with all outputs disabled, so the project's `robot.toml` and profiles apply. It SHALL report `[ ERROR ]` lines and missing-keyword or argument failures as non-blocking additional context, capped like the deprecation feedback. It is off by default. When `robotcode` is not available, the dry run SHALL be skipped silently, like the other tiers.

#### Scenario: Unknown keyword surfaced when enabled
- **WHEN** the flag is set and the agent writes a test that calls a keyword that no import provides
- **THEN** the hook adds the dry-run "No keyword with name" message as additional context and exits 0 unless another tier found a blocking error

#### Scenario: Disabled by default
- **WHEN** the flag is not set
- **THEN** no `robotcode` or `robot` process is started for the dry run

#### Scenario: Profile settings apply
- **WHEN** the flag is set and the project's `robot.toml` adds a `python-path` entry that a suite's library import needs
- **THEN** the dry run resolves that import and reports no import error
