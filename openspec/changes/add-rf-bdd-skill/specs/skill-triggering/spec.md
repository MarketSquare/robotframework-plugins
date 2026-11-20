## MODIFIED Requirements

### Requirement: Sibling skills state their boundary

Each skill that has a sibling covering a similar task SHALL name that sibling, based on an observable signal, in a "When to use" block within the first 20 lines of its `SKILL.md` body; compact descriptions have no room for it. The block SHALL also list the concrete trigger terms (import lines, file names, CLI names, pasted errors and symptoms) that no longer fit in the description.

The sibling pairs and signals are:
- rf-browser ↔ rf-selenium: the imported library (`Browser` vs `SeleniumLibrary`), or Playwright vs WebDriver/Selenium Grid.
- rf-requests ↔ rf-restinstance: the imported library (`RequestsLibrary` vs `REST`), or JSON Schema/OpenAPI-driven assertions.
- rf-language ↔ the robotcode plugin's `robotcode` skill: writing Robot Framework syntax vs running, discovering, looking up, analysing or debugging with the robotcode CLI. rf-language names the robotcode skill by its plugin, outside its Companion Skills table.
- rf-language ↔ rf-bdd: Robot Framework syntax, keyword-driven and data-driven tests vs a BDD specification. The BDD signals are Given/When/Then scenarios written as a specification, pasted Gherkin or acceptance criteria, step-vocabulary design, and reviewing the readability of BDD suites. rf-bdd says that it relies on rf-language for syntax, so loading both is expected.
- rf-setup ↔ the library skills: installing and fixing the environment vs writing and fixing test code.

#### Scenario: Web siblings reference each other
- **WHEN** the "When to use" blocks of rf-browser and rf-selenium are read
- **THEN** rf-browser names rf-selenium for SeleniumLibrary/WebDriver projects, and rf-selenium names rf-browser for Browser Library/Playwright projects

#### Scenario: API siblings reference each other
- **WHEN** the "When to use" blocks of rf-requests and rf-restinstance are read
- **THEN** each names the other together with the library import that selects it

#### Scenario: Script skills defer to robotcode
- **WHEN** the "When to use" blocks of all shipped skills are read
- **THEN** none names `rf-results`, `rf-libdoc` or `rf-robotcode` as a sibling or fallback

#### Scenario: Language skill defers CLI work to robotcode
- **WHEN** the "When to use" block of rf-language is read
- **THEN** it says that running, discovering, keyword lookup, result reading and debugging with the robotcode CLI are covered by the robotcode plugin's `robotcode` skill

#### Scenario: Language and BDD siblings reference each other
- **WHEN** the "When to use" blocks of rf-language and rf-bdd are read
- **THEN** rf-language names rf-bdd for BDD specifications, and rf-bdd names rf-language for Robot Framework syntax

#### Scenario: Setup is separated from test writing
- **WHEN** the "When to use" block of rf-setup is read
- **THEN** it lists installation and environment error triggers and says that writing tests belongs to the library skills

### Requirement: Sibling skills share a plugin

Skills that the "Sibling skills state their boundary" requirement pairs as siblings for the same task SHALL ship in the same plugin, so that a user who has one also has the boundary text of the other. These pairs are rf-browser and rf-selenium, rf-requests and rf-restinstance, and rf-language and rf-bdd.

#### Scenario: Web siblings together
- **WHEN** the catalogue is listed
- **THEN** `rf-browser` and `rf-selenium` are both in `rf-web`, and `rf-requests` and `rf-restinstance` are both in `rf-api`

#### Scenario: Language siblings together
- **WHEN** the catalogue is listed
- **THEN** `rf-language` and `rf-bdd` are both in `rf-core`
