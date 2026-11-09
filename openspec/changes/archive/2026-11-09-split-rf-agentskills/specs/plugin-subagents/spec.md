## MODIFIED Requirements

### Requirement: Subagents route to the owning skills

Each subagent SHALL contain a routing table. The table maps the kinds of work the subagent delegates to the skill that owns them, or to the robotcode command that answers them, using the skill identifiers of the shipped catalog. Routes:
- test-case and suite design, user keywords, resources, variables and legacy-syntax migration SHALL route to `rf-language`;
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

#### Scenario: Debug expert routes a library-side failure
- **WHEN** `rf-debug-expert` diagnoses "library contains no keywords" or state that resets between tests
- **THEN** its routing table sends that failure class to `rf-python-library`

#### Scenario: Every routed skill exists
- **WHEN** the subagent lint test compares the skill identifiers named in all subagent files with the skill directories of every catalogue plugin
- **THEN** every named skill exists, each one outside `rf-core` is named with its plugin, and no retired or merged-away name appears (`rf-keyword-builder`, `rf-testcase-builder`, `rf-resource-architect`, `rf-libdoc-search`, `rf-libdoc-explain`, `rf-libdoc`, `rf-results`, `rf-robotcode`, `rf-keyword-consultant`, and any `robotframework-*` identifier)

#### Scenario: Missing library skill
- **WHEN** only `rf-core` is installed and `rf-migration-guide` is asked to move a suite from SeleniumLibrary to Browser
- **THEN** it says that the steps come from `rf-browser` in the `rf-web` plugin and suggests installing that plugin, before changing any library-specific code

### Requirement: Subagents do not duplicate skill content

Subagent files SHALL NOT contain keyword catalogs, standard-library quick references, RF syntax tables, robotcode command references, library-to-library migration tables or long code examples that a routed skill or the robotcode plugin already provides. Library-to-library migration tables SHALL live in the target library's skill, for example SeleniumLibrary to Browser in `rf-browser`. Each subagent body SHALL stay within 120 lines. A subagent MAY keep content that no skill owns, such as library-selection criteria or a failure taxonomy. It SHALL mark that content as the subagent's own.

#### Scenario: Debug expert keeps only its own method
- **WHEN** `rf-debug-expert.md` is read
- **THEN** it contains its failure taxonomy, flakiness table and report format, marked as agent-owned, and no copy of the robotcode `results` or `robot-debug` option reference

#### Scenario: Keyword consultant has no catalog
- **WHEN** `plugins/rf-core/agents/` and the generated variants are listed
- **THEN** no `rf-keyword-consultant` file exists, so no cross-library keyword map or standard-library keyword list is shipped as a subagent

#### Scenario: Size budget is enforced
- **WHEN** the subagent lint test counts the lines of each subagent body (excluding frontmatter)
- **THEN** every body has 120 lines or fewer

#### Scenario: Migration tables live in library skills
- **WHEN** `rf-migration-guide.md` is searched for a SeleniumLibrary-to-Browser or RequestsLibrary-to-RESTinstance keyword table
- **THEN** none is found, and `rf-browser` and `rf-restinstance` each ship the table as a reference
