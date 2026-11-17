## Purpose

Keep the repository's own tooling on the RobotCode CLI for core Robot Framework capabilities (running, discovery, analysis, results, keyword documentation), enforce it with an automated guard, and send capability gaps upstream to RobotCode instead of re-implementing them here.

## ADDED Requirements

### Requirement: Tooling uses RobotCode for core Robot Framework capabilities

Repository tooling (files under `scripts/`, `src/`, `plugins/*/scripts/`, `plugins/*/skills/*/scripts/` and `plugins/*/hooks/`) SHALL use the `robotcode` CLI to run suites (`robotcode robot`), discover suites and tests (`robotcode discover`), analyse Robot Framework code (`robotcode analyze code`), read run results (`robotcode results`) and read library or keyword documentation (`robotcode doc`). It SHALL NOT re-implement these capabilities with Robot Framework's Python API or by starting `robot`, `rebot` or `libdoc` directly, unless an allowlist entry covers the use. Custom code SHALL remain allowed for what RobotCode does not provide, such as Markdown extraction, hook integration, project-convention detection, library-author checks and eval grading logic.

#### Scenario: Results read through RobotCode
- **WHEN** a grader needs the pass, fail and skip counts or failure messages of a finished run
- **THEN** it reads them from `robotcode results summary` or `robotcode results show` with `--format json`, not by parsing `output.xml`

#### Scenario: Custom value stays custom
- **WHEN** a skill script detects project naming conventions with the Robot Framework parser
- **THEN** the use is allowed through an allowlist entry whose reason states that RobotCode has no such capability

### Requirement: Automated guard with a reasoned allowlist

The repository SHALL provide a deterministic check that scans the tooling paths for direct uses of Robot Framework APIs and commands that RobotCode covers: `robot.libdoc`/`robot.libdocpkg`/`LibraryDocumentation`, `ExecutionResult` and XML parsing of result files (`xml.etree`/`ElementTree`), `TestSuiteBuilder`, `get_model`/`ModelVisitor`, and process calls that start `robot`, `rebot` or `libdoc` (including `-m robot`). It SHALL exit non-zero for any use that no allowlist entry covers, naming the file, line and pattern. Each allowlist entry SHALL name the file, the pattern and a reason. An entry that matches nothing SHALL fail the check. The check SHALL run in CI on every pull request and in the pytest suite, and SHALL need no human review to pass or fail.

#### Scenario: New re-implementation fails
- **WHEN** a pull request adds `from robot.api import ExecutionResult` to a file under `src/` that no allowlist entry covers
- **THEN** the check exits non-zero and names the file, the line and the pattern

#### Scenario: Allowlisted use passes
- **WHEN** `plugins/rf-core/skills/rf-python-library/scripts/check_library.py` uses `LibraryDocumentation` and an allowlist entry for that file and pattern gives the reason
- **THEN** the check passes for that use

#### Scenario: Stale entry fails
- **WHEN** an allowlist entry names a file or pattern that no longer occurs
- **THEN** the check fails and names the stale entry

#### Scenario: Robocop is not flagged
- **WHEN** a hook runs `robocop check`
- **THEN** the check does not report it, because Robocop is part of `robotcode[all]` and RobotCode does not replace it

### Requirement: RobotCode gaps are reported upstream

When repository tooling needs a Robot Framework capability that RobotCode lacks or gets wrong, the change that meets the need SHALL record the gap in its design with the RobotCode version tested and a minimal reproduction, and SHALL draft an issue for `robotcodedev/robotcode`. A maintainer SHALL review each draft before it is filed, and the filed issue SHALL carry the AI disclosure that RobotCode's AI policy asks for. A local workaround SHALL be allowlisted with a reason that links the issue, so it is removed when RobotCode closes the gap.

#### Scenario: Workaround linked to its issue
- **WHEN** tooling keeps a workaround for a RobotCode gap
- **THEN** its allowlist entry's reason contains the URL of the RobotCode issue
