## MODIFIED Requirements

### Requirement: Scope boundaries with sibling skills

The skill SHALL NOT teach these topics, which belong elsewhere:
- Python keyword libraries or listeners (rf-python-library);
- library-specific keywords, locators or waits (the library skills);
- installation (rf-setup);
- BDD specification design (rf-bdd): mapping features, rules and examples onto suites, documentation and tags; step vocabularies and scenario state; translating Gherkin; reviewing BDD readability;
- driving the robotcode CLI: running, discovery, keyword documentation, result analysis, debugging.

The BDD mechanics stay in this skill: prefix stripping, prefix-free step definitions and embedded arguments. Where a task crosses into a topic listed above, the skill SHALL name the sibling skill, or for robotcode CLI work the robotcode plugin's `robotcode` skill. Its code blocks SHALL call only BuiltIn or standard-library keywords and keywords defined in the example resources.

The gotcha about keyword-call casing SHALL tell the agent to follow the casing the project's Robocop configuration and existing keywords use, and SHALL NOT require Title Case for BDD steps.

#### Scenario: No library keyword catalogue
- **WHEN** the skill's code blocks are checked
- **THEN** they call only BuiltIn or standard-library keywords and keywords defined in the example resources

#### Scenario: BDD specification work is handed to rf-bdd
- **WHEN** the `When to use` block, `references/styles.md` and the BDD part of `references/embedded-arguments.md` are read
- **THEN** each names `rf-bdd` for writing or reviewing BDD specifications, in one line

#### Scenario: Casing follows the project
- **WHEN** the `Gotchas` section is read
- **THEN** no item requires Title Case for `Given`/`When`/`Then` steps, and the casing item says to follow the project's Robocop configuration

### Requirement: Companion Skills integration

`SKILL.md` SHALL end with a `## Companion Skills` `Need | Skill` table with rows for:
- rf-python-library (only once shipped in the same release);
- at least rf-browser and rf-requests as library skills;
- rf-setup;
- rf-bdd.

A sentence after the table SHALL name the robotcode plugin's `robotcode` skill for running, keyword lookup, result analysis and debugging. The Companion Skills tables of rf-setup, rf-python-library, rf-bdd, rf-browser, rf-selenium, rf-appium, rf-requests, rf-restinstance and rf-platynui SHALL each get one row naming `rf-language`, with identical Need wording from the shared catalogue key `language`.

#### Scenario: Table rows present
- **WHEN** the rf-language Companion Skills table is parsed
- **THEN** it has rows naming rf-python-library, rf-browser, rf-requests, rf-setup and rf-bdd, no row names rf-libdoc, rf-results or rf-robotcode, and every named skill is shipped in the same release

#### Scenario: Other skills point back
- **WHEN** the Companion Skills tables of the nine skills listed above are parsed
- **THEN** each has a row naming `rf-language` with identical Need wording, and no table names `rf-test-design`, `rf-keyword-design` or a retired skill
