## MODIFIED Requirements

### Requirement: Context injection routes by task

When the user prompt contains a Robot Framework signal, the `UserPromptSubmit` hook SHALL inject one additional-context message. The message SHALL route by kind of work:
- tests, suites, user keywords, resources and variables to `rf-language`;
- Given/When/Then specifications and Gherkin input to `rf-bdd`;
- Python libraries and listeners to `rf-python-library`;
- library usage to the library's own skill, without naming it, and to installing the technology plugin (`rf-web`, `rf-api`, `rf-mobile`, `rf-desktop`) when that skill is not available;
- keyword names and arguments to `robotcode doc keyword`, instead of memory;
- run results to `robotcode results`, instead of reading `output.xml`.

The message SHALL end with a one-line reminder to write RF 7 syntax (`RETURN`, `VAR`, `IF`, `Test Tags`).

#### Scenario: RF prompt gets the routing message
- **WHEN** the prompt is "add a data-driven login test to tests/login.robot"
- **THEN** the hook emits exactly one `UserPromptSubmit` additional-context message that names `rf-language`, `rf-bdd`, `rf-python-library`, `robotcode doc` and `robotcode results`

#### Scenario: Non-RF prompt gets nothing
- **WHEN** the prompt contains no Robot Framework signal (e.g. "refactor this React component")
- **THEN** the hook emits nothing and exits 0

### Requirement: Injection trigger covers current skills and RF source

The trigger SHALL match case-insensitively:
- existing RF signals: the framework name, the `.robot` and `.resource` extensions, library names, and tooling names such as libdoc, robocop and robotcode;
- the identifiers of the shipped skills and subagents, including `rf-language`, `rf-bdd`, `rf-python-library` and `rf-setup`;
- RF section headers pasted into the prompt (`*** Settings ***`, `*** Variables ***`, `*** Test Cases ***`, `*** Tasks ***`, `*** Keywords ***`).

It SHALL NOT match bare "test", bare "RF", or Gherkin keywords such as "Given" or "Scenario" on their own.

#### Scenario: New skill name triggers
- **WHEN** the prompt is "use rf-python-library to build a listener"
- **THEN** the hook injects the message

#### Scenario: BDD skill name triggers
- **WHEN** the prompt is "use rf-bdd to turn these acceptance criteria into tests"
- **THEN** the hook injects the message

#### Scenario: Pasted RF source triggers
- **WHEN** the prompt contains a line `*** Keywords ***`
- **THEN** the hook injects the message

#### Scenario: Bare words do not trigger
- **WHEN** the prompt is "run the unit tests and fix the RF amplifier model"
- **THEN** the hook emits nothing

#### Scenario: Plain Gherkin does not trigger
- **WHEN** the prompt is "write Cucumber step definitions in Java for: Given a cart, When I check out"
- **THEN** the hook emits nothing
