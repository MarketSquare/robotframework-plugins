## ADDED Requirements

### Requirement: Static keyword resolution counts library calls through user keywords

The `keywords_resolve` check SHALL count, for `min_calls`, the calls into spec-covered libraries that the suite's tests and fixtures reach. A library call written directly in a test or fixture SHALL count once. A call of a user keyword (from the suite or its resources) SHALL count every library call reached through that keyword's body, following nested user keywords. A user keyword that is reached again while its own body is being counted SHALL add nothing more, so recursive keywords terminate. User keywords that no test or fixture calls SHALL NOT add to the count. Standard-library calls SHALL NOT count. The check's summary SHALL report the number of call sites, the number of library call sites and the counted library calls.

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

### Requirement: PlatynUI tasks check locators statically

PlatynUI eval tasks SHALL include a gating static locator check on the produced suite. The check SHALL fail when an XPath in the suite, its resources or its variables uses a plain `@AutomationId` attribute (PlatynUI exposes the UIA AutomationId as `@Id`; `@native:AutomationId` stays allowed), or when a control that the fixture README gives an `@Id` for is located only by an English `@Name` value. Its failure message SHALL name the offending locator and the attribute to use instead. In a partial-install task, the locator check SHALL be part of the fallback check that passes the task when no plugin is suggested.

#### Scenario: Plain AutomationId rejected
- **WHEN** a suite locates the result display with `//control:Text[@AutomationId='CalculatorResults']`
- **THEN** the locator check fails and its message names that locator and `@Id`

#### Scenario: Id locators accepted
- **WHEN** a suite locates the buttons with `@Id='num1Button'`, `@Id='plusButton'`, `@Id='equalButton'` and the display with `@Id='CalculatorResults'`
- **THEN** the locator check passes

#### Scenario: Language-bound name rejected
- **WHEN** a suite clicks the digit buttons only through `//control:Button[@Name='One']` and `@Name='Two'`
- **THEN** the locator check fails and names the `@Id` the README gives for those buttons

#### Scenario: Partial task falls back to both checks
- **WHEN** a partial-install session doesn't suggest rf-desktop and writes a suite whose keywords resolve but that uses `@AutomationId`
- **THEN** the task fails

### Requirement: Manual live check of desktop suites

The repository SHALL document and ship a manual live check for rf-desktop. On a Windows desktop session, it SHALL run the PlatynUI suites from a downloaded eval run's artifacts and the skill's example suite against the real application, one fresh application instance per suite, with a per-suite time limit. It SHALL report pass counts per tier and arm, and the most common failure messages. It SHALL NOT run in CI, and it SHALL refuse to run a suite that imports a library other than `PlatynUI.BareMetal` and the standard libraries `BuiltIn`, `Collections`, `String` and `Process` (for the skill example only), or that calls `Evaluate`, `Run Process` or file-system keywords.

#### Scenario: Report per arm
- **WHEN** the check runs on the artifacts of a full eval run on a Windows desktop
- **THEN** it prints, for narrow and partial and each arm, how many suites passed against the real Calculator, and the skill example's result

#### Scenario: Unsafe suite skipped
- **WHEN** a collected suite imports `OperatingSystem` or calls `Evaluate`
- **THEN** the check doesn't run it and lists it as skipped with the reason
