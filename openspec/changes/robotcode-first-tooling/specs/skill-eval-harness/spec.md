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

## MODIFIED Requirements

### Requirement: Static keyword resolution counts library calls through user keywords

The `keywords_resolve` check SHALL count, for `min_calls`, the calls into imported non-standard libraries that the suite's tests and fixtures reach, with each library's keyword names read from `robotcode doc keywords --format json`. A library call written directly in a test or fixture SHALL count once. A call of a user keyword (from the suite or its resources) SHALL count every library call reached through that keyword's body, following nested user keywords. A user keyword that is reached again while its own body is being counted SHALL add nothing more, so recursive keywords terminate. User keywords that no test or fixture calls SHALL NOT add to the count. Standard-library calls SHALL NOT count. The check's summary SHALL report the number of call sites, the number of library call sites and the counted library calls.

#### Scenario: Library keyword wrapped in a user keyword
- **WHEN** a suite defines `Press Digit` whose body calls `Pointer Click` once, its test calls `Press Digit` three times and calls `Get Attribute` once, and the check has `min_calls: 4`
- **THEN** the counted library calls are 4 and the `min_calls` condition passes

#### Scenario: BuiltIn-only suite still fails
- **WHEN** a suite imports the required library but its tests only call `Log` and `Should Be Equal`
- **THEN** the counted library calls are 0 and the check fails with a message naming the expected minimum

#### Scenario: Unused user keyword adds nothing
- **WHEN** a suite defines a user keyword that calls four library keywords, but no test or fixture calls it
- **THEN** that keyword's calls do not count toward `min_calls`

#### Scenario: Recursive user keyword terminates
- **WHEN** a user keyword calls itself and one library keyword
- **THEN** the check finishes and counts that library call once per call from a test
