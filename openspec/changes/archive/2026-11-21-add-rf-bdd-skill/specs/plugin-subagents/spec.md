## MODIFIED Requirements

### Requirement: Subagents route to the owning skills

Each subagent SHALL contain a routing table. The table maps the kinds of work the subagent delegates to the skill that owns them, or to the robotcode command that answers them, using the skill identifiers of the shipped catalog. Routes:
- test-case and suite design, user keywords, resources, variables and legacy-syntax migration SHALL route to `rf-language`;
- BDD specifications (Given/When/Then suites, step vocabularies, translating Gherkin or acceptance criteria) SHALL route to `rf-bdd`;
- Python keyword libraries and listeners SHALL route to `rf-python-library`;
- keyword name and argument lookup SHALL route to `robotcode doc keywords` / `robotcode doc keyword`;
- reading results SHALL route to `robotcode results`;
- step debugging SHALL route to `robotcode robot-debug -bl "<longname>"`;
- library-specific behavior, and migration from one library to another, SHALL route to the matching library skill, naming its plugin;
- environment problems SHALL route to `rf-setup`.

When a routed library skill is not available, the subagent SHALL name the plugin to install and SHALL NOT continue from memory for library-specific details.

#### Scenario: Test architect delegates design details
- **WHEN** `rf-test-architect` has decided the project layout and must write test suites and shared keywords
- **THEN** its instructions direct it to load `rf-language` for the suites and the resource files, and not to follow an inline syntax guide

#### Scenario: Test architect delegates BDD specifications
- **WHEN** `rf-test-architect` is asked to set up acceptance tests written as Given/When/Then specifications
- **THEN** its routing table sends the suites and step keywords to `rf-bdd`

#### Scenario: Debug expert routes a library-side failure
- **WHEN** `rf-debug-expert` diagnoses "library contains no keywords" or state that resets between tests
- **THEN** its routing table sends that failure class to `rf-python-library`

#### Scenario: Every routed skill exists
- **WHEN** the subagent lint test compares the skill identifiers named in all subagent files with the skill directories of every catalogue plugin
- **THEN** every named skill exists, each one outside `rf-core` is named with its plugin, and no retired or merged-away name appears (`rf-keyword-builder`, `rf-testcase-builder`, `rf-resource-architect`, `rf-libdoc-search`, `rf-libdoc-explain`, `rf-libdoc`, `rf-results`, `rf-robotcode`, `rf-keyword-consultant`, and any `robotframework-*` identifier)

#### Scenario: Missing library skill
- **WHEN** only `rf-core` is installed and `rf-migration-guide` is asked to move a suite from SeleniumLibrary to Browser
- **THEN** it says that the steps come from `rf-browser` in the `rf-web` plugin and suggests installing that plugin, before changing any library-specific code
