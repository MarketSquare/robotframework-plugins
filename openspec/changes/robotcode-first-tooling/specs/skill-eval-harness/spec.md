## ADDED Requirements

### Requirement: Grader runs and reads results through RobotCode

Grader checks that run a produced suite (`robot_pass`, `robot_dryrun` and the custom graders that run hidden suites) SHALL start the run with `robotcode robot` from the workspace and SHALL read pass, fail and skip counts and failure messages from `robotcode results` with `--format json`. A check whose run needs a Robot Framework version other than the harness's own MAY start that version through `uvx`, with `robotcode` in the same environment where its runner supports that version; otherwise the use SHALL be allowlisted with a reason. When `robotcode` is not installed in the grader environment, the check SHALL be `skipped`, never `passed`.

#### Scenario: Counts from RobotCode
- **WHEN** a produced suite has one passing, one failing and one skipped test and a `robot_pass` check runs on it
- **THEN** the verdict details report `tests=3 passed=1 failed=1` and the check fails

#### Scenario: RobotCode missing
- **WHEN** `robotcode` is not on the grader's PATH or next to its interpreter
- **THEN** `robot_pass` and `robot_dryrun` return `skipped` with a reason naming `robotcode`

### Requirement: Static keyword resolution uses the installed libraries

The `keywords_resolve` check SHALL resolve the produced suite's keyword calls with `robotcode analyze code` against the libraries installed in the grader environment, and SHALL NOT read libdoc spec files. A `KeywordNotFound` or argument error in the suite, or a failed import of a library the task requires, SHALL fail the check. For `min_calls`, a library call SHALL be a call to a keyword of an imported library that is not a Robot Framework standard library, with the library's keyword names taken from `robotcode doc keywords --format json`. Task YAMLs SHALL NOT have `spec_dir` or `specs` params, and the repository SHALL NOT keep libdoc spec files for grading.

#### Scenario: PlatynUI resolves without a desktop
- **WHEN** the grader environment has `robotframework-PlatynUI` installed, runs on Linux without a display, and the produced suite imports `PlatynUI.BareMetal` and calls `Pointer Click`
- **THEN** the check resolves the call and counts it as one library call

#### Scenario: Misspelled keyword fails
- **WHEN** the produced suite calls `Convert To Uper Case`
- **THEN** the check fails and its details name the keyword and the `KeywordNotFound` diagnostic

#### Scenario: Spec params rejected
- **WHEN** a task YAML gives `keywords_resolve` a `specs` param
- **THEN** task validation fails and names the param
