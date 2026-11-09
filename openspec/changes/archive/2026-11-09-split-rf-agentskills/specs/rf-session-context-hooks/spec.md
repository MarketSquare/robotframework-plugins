## MODIFIED Requirements

### Requirement: Context injection routes by task

When the user prompt contains a Robot Framework signal, the `UserPromptSubmit` hook SHALL inject one additional-context message. The message SHALL route by kind of work:
- tests, suites, user keywords, resources and variables to `rf-language`;
- Python libraries and listeners to `rf-python-library`;
- library usage to the library's own skill, without naming it, and to installing the technology plugin (`rf-web`, `rf-api`, `rf-mobile`, `rf-desktop`) when that skill is not available;
- keyword names and arguments to `robotcode doc keyword`, instead of memory;
- run results to `robotcode results`, instead of reading `output.xml`.

The message SHALL end with a one-line reminder to write RF 7 syntax (`RETURN`, `VAR`, `IF`, `Test Tags`).

#### Scenario: RF prompt gets the routing message
- **WHEN** the prompt is "add a data-driven login test to tests/login.robot"
- **THEN** the hook emits exactly one `UserPromptSubmit` additional-context message that names `rf-language`, `rf-python-library`, `robotcode doc` and `robotcode results`

#### Scenario: Non-RF prompt gets nothing
- **WHEN** the prompt contains no Robot Framework signal (e.g. "refactor this React component")
- **THEN** the hook emits nothing and exits 0

### Requirement: Injection names only shipped skills

The injected message SHALL name only skills and subagents shipped by `rf-core`, the plugin that ships the hook, so that every name it gives is installed. It MAY name technology plugins. It SHALL NOT name retired or merged-away skills or subagents (`keyword-builder`, `testcase-builder`, `resource-architect`, `libdoc-search`, `libdoc-explain`, `rf-libdoc`, `rf-results`, `rf-robotcode`, `rf-keyword-consultant`) or pre-rename identifiers. robotcode commands are named as commands, not as skills.

#### Scenario: Catalog consistency
- **WHEN** the hook test extracts every skill-like identifier from the injected message
- **THEN** each one is a directory under `plugins/rf-core/skills/`, a file under `plugins/rf-core/agents/`, or the name of a catalogue plugin

## ADDED Requirements

### Requirement: Environment report names the plugin for each detected library

When the `SessionStart` environment report finds a library in the project environment that a technology plugin covers, it SHALL name that plugin once, with the command that installs it for the current agent where one exists. It SHALL NOT tell the user to install a plugin for a library the project doesn't use. The report SHALL still always exit 0.

#### Scenario: Browser found
- **WHEN** the session starts in a project whose environment has the `Browser` library
- **THEN** the report says that `rf-web` covers it, and shows `/plugin install rf-web@robotframework-plugins` in Claude Code

#### Scenario: Nothing to suggest
- **WHEN** the project's environment has Robot Framework and no library that a plugin covers
- **THEN** the report names no technology plugin
