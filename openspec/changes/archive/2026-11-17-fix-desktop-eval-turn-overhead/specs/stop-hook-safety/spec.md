## ADDED Requirements

### Requirement: Test reminder is skipped once the suite has run

The `maybe_remind_robot_tests.mjs` reminder SHALL NOT be emitted when the session transcript shows a Robot Framework run (`robot`, `python -m robot`, `robotcode robot`, with or without `--dryrun`) after the last tool call that wrote a `.robot` or `.resource` file. When it is emitted, its first step SHALL say to run the affected tests where they can run, so an agent on a machine that cannot run them does not keep trying.

#### Scenario: Suite dry-run after the last write
- **WHEN** a session writes `tests/calculator.robot` and then runs `robot --dryrun tests/calculator.robot`
- **THEN** the Stop hook emits no reminder

#### Scenario: Write after the last run
- **WHEN** a session runs `robot tests/` and later edits `tests/login.robot` without running it again
- **THEN** the Stop hook emits the reminder (subject to the once-per-session rule)

#### Scenario: Reminder wording
- **WHEN** the reminder is emitted
- **THEN** its first step tells the agent to run the affected tests where they can run
