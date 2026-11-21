# bdd-skill Specification

## Purpose
Provide the `rf-bdd` agent skill. It teaches agents to write and review behaviour-driven Robot Framework specifications in native `.robot` and `.resource` files. Features, rules and examples map onto suites, documentation, metadata and tags. One step vocabulary serves every suite, and state lives in a declared place. Outlines become templates only when one sentence fits every row, and pasted Gherkin is translated by meaning. It relies on `rf-language` for Robot Framework syntax and on the robotcode plugin for running and analysing.

## Requirements

### Requirement: Skill exists with conformant frontmatter and layout

The skill SHALL live at `plugins/rf-core/skills/rf-bdd/` with `SKILL.md` whose `name` is `rf-bdd`. Its frontmatter SHALL satisfy the skill-metadata-conformance rules:
- `license: Apache-2.0`;
- a `compatibility` field naming Python 3.8+, `robotframework>=7` and `robotcode[all]>=2.8` in the project environment;
- `metadata.author`, and no `metadata.version` (a skill's version is its plugin's).

The skill SHALL contain `SKILL.md`, a `references/` folder and an `assets/` folder. It SHALL contain no `scripts/` folder and no `allowed-tools` field.

#### Scenario: Frontmatter validates
- **WHEN** `python scripts/validate-skills.py --channel all` runs
- **THEN** `rf-bdd` passes every frontmatter rule and has no `metadata.version`

#### Scenario: Skill is shipped by rf-core
- **WHEN** `python scripts/build-catalog.py --check` runs
- **THEN** `rf-bdd` is listed once, in `rf-core`

### Requirement: Description is compact and draws the BDD boundary

The `description` SHALL:
- be at most 160 characters;
- name Robot Framework (or RF);
- name BDD or Given/When/Then;
- carry a load cue starting with "Use" or "Load";
- name no more than 2 keyword or API names;
- contain no meta-phrasing about the agent or the skill.

All shipped rf-* descriptions together SHALL stay within the listing room that `tests/test_skill_descriptions.py` enforces.

#### Scenario: Compact contract passes
- **WHEN** `tests/test_skill_descriptions.py` runs
- **THEN** rf-bdd passes the compact description checks, and the listing total stays within the limit

### Requirement: When to use block names the sibling and the trigger terms

Within the first 20 lines of the `SKILL.md` body, a `## When to use` block SHALL:
- list the trigger terms that don't fit in the description: "BDD style", "Given/When/Then", "executable specification", "acceptance criteria", "Gherkin" or "Cucumber" pasted as input, "scenario outline", "Background", and reviewing the readability or consistency of tests or step keywords;
- name `rf-language` as the sibling, with its signal: plain Robot Framework syntax, keyword-driven or data-driven tests without a specification, resources and variables;
- say that `rf-bdd` relies on `rf-language` for syntax details;
- name the robotcode plugin's `robotcode` skill for running, discovery, keyword lookup and result reading.

#### Scenario: Sibling named with signal
- **WHEN** the first 20 body lines of `SKILL.md` are read
- **THEN** they contain a `## When to use` heading, name `rf-language` with its signal, and name the `robotcode` skill of the robotcode plugin

### Requirement: SKILL.md skeleton and size budget

`SKILL.md` SHALL contain these level-2 sections in this order:
- `When to use`;
- `Version gate`;
- `Step 0: Match the project`;
- `House rules`;
- `Write a specification`;
- `Review a specification`;
- `Gherkin input`;
- `Gotchas`;
- `When to read the references`;
- `Companion Skills`.

An orientation of at most about 5 lines before `When to use` SHALL end with one line `Verified against Robot Framework <version>`. `SKILL.md` SHALL be at most 500 lines including frontmatter. It SHOULD be at most 300 lines; the structure test warns above 300.

#### Scenario: Sections ordered
- **WHEN** the structure test parses the level-2 headings
- **THEN** every required heading is present, in the order given

#### Scenario: Budget enforced
- **WHEN** the structure test counts the lines of `SKILL.md`
- **THEN** it fails above 500 lines and warns above 300

### Requirement: References are gated, shallow and do not duplicate rf-language

The skill SHALL ship exactly these references:
- `references/gherkin-mapping.md`: feature, rule, scenario, background, outline, examples, step arguments (`key=value` and list arguments), and a mapping table for Gherkin-only constructs;
- `references/step-design.md`: sentence rules, naming, declarative steps, embedded-argument design for steps, catch-all and ambiguous steps, vocabulary reuse, `robot:private`;
- `references/state.md`: the resource strategy (variables declared in `*** Variables ***`, never mutated in place) and the World-library strategy (`@library(scope="TEST")`), with the leak example;
- `references/data-driven.md`: the ladder from single scenario to `Test Template` to `[Template]` to DataDriver, the rule that an outline sentence fits every row, and the data-driven smells;
- `references/documentation-and-tags.md`: suite and test documentation, `Metadata`, feature and rule tags, `tag-doc`/`tag-stat-link`, and localisation (`Language:`) with natural word order;
- `references/robocop.md`: the Robocop asset, what each setting does, how to merge it into an existing configuration, and the repeated-`--select` rule;
- `references/review-checklist.md`: the review checks with IDs and the findings format.

Every reference SHALL be linked from the `When to read the references` table with a "read when" condition. References SHALL NOT link to other reference files or to paths in another skill. Every reference over 100 lines SHALL list its level-2 sections within its first 15 lines.

Generic Robot Framework mechanics SHALL be stated in `rf-bdd` only as a one-line rule that names `rf-language`. These are embedded-argument matching and conflicts, template mechanics and status rules, tag patterns and selection, and `__init__.robot` visibility.

#### Scenario: Reference set matches the table
- **WHEN** the structure test compares `references/*` with the reference table
- **THEN** the two sets are equal and contain exactly the seven files named above

#### Scenario: No duplicated syntax tutorial
- **WHEN** the references are searched for the generic topics listed above
- **THEN** each occurrence is a one-line rule that names `rf-language`, not a full explanation

### Requirement: Version gate before version-dependent syntax

The `Version gate` section SHALL tell the agent to establish the project's Robot Framework version before writing version-dependent syntax. It SHALL list at least:
- typed embedded arguments `${n: int}` and typed `[Arguments]` (7.3), with a regex pattern plus explicit conversion as the form for older versions;
- BDD prefix stripping before a leading embedded argument (7.1);
- `VAR … scope=TEST` (7.0);
- test-level `[Metadata]` (7.5), with suite `Metadata` or documentation as the form for older versions.

#### Scenario: Older version gets compatible forms
- **WHEN** the agent works in a project pinned to Robot Framework 7.1
- **THEN** the skill directs it to use `${n:\d+}` with explicit conversion instead of `${n: int}`, and no test-level `[Metadata]`

### Requirement: Step 0 follows the project's conventions before the skill's defaults

`Step 0: Match the project` SHALL tell the agent to detect the project's conventions before writing, with `rf-language`'s Step 0 or the documented fallback searches. The agent SHALL then follow what it finds:
- step-keyword casing;
- the import style (by name through `python-path`, or relative paths);
- the state strategy (resource variables or a World library);
- the existing step vocabulary (`robotcode doc keywords` on the steps resources);
- the tag vocabulary.

Only when the project has no convention for an item SHALL the skill's default apply:
- sentence-style step names, with only the first word capitalized, plus `assets/robocop-bdd.toml` merged into the project's Robocop configuration;
- imports by name, with the folder on `python-path`;
- the resource strategy.

The skill SHALL NOT reference a path into another skill's directory.

#### Scenario: Title Case project is respected
- **WHEN** the project's existing step keywords are Title Case (`The Cart Contains ${count} Items`)
- **THEN** the new step keywords the agent writes are Title Case too, and the agent doesn't change the project's Robocop configuration

#### Scenario: Greenfield project gets the defaults
- **WHEN** the project has no step keywords and no Robocop configuration
- **THEN** the agent writes sentence-style step names, adds the Robocop settings from `assets/robocop-bdd.toml` to the project configuration, and imports the steps resource by name with its folder on `python-path`

### Requirement: House rules state the specification design

The `House rules` section SHALL state these rules, each with its reason:
1. three keyword layers (steps, domain keywords, technical keywords) and `robot:private` for helpers;
2. one behaviour per test, with one `When`;
3. domain language, not UI or implementation detail;
4. step naming (casing from Step 0; values as quoted or pattern-restricted embedded arguments);
5. one vocabulary across suites, extended rather than duplicated;
6. the Gherkin mapping: feature to suite or feature directory, rule to documentation and tag, outline to template only when one sentence fits every row, no `IF` in a template keyword;
7. state in the declared place, never mutating a declared container in place;
8. independent tests;
9. living documentation: suite documentation, `Metadata Feature`, feature and rule tags;
10. imports by the project's convention;
11. style tooling with Robocop, using the project's configuration.

#### Scenario: Rules present
- **WHEN** the structure test parses the `House rules` section
- **THEN** it finds 11 numbered rules, which mention `robot:private`, one `When`, `Test Template`, `IF`, `Metadata` and Robocop

### Requirement: Write, Review and Gherkin-input modes

The skill SHALL define three modes:
- **Write**: discover the vocabulary, draft the specification (feature, rules, scenarios), then the steps and lower layers. Validate with `robotcode analyze code`, a dry run, a real run of the affected tests by longname, and Robocop. Report the files and any convention the agent followed or added.
- **Review**: read the suites and steps, apply `references/review-checklist.md`, and report findings with check IDs, file and line. The agent SHALL NOT edit files in review mode unless the user asks.
- **Gherkin input**: translate pasted Gherkin or acceptance criteria into native `.robot` suites. The agent SHALL keep every rule and every example. It SHALL split an Examples row whose sentence doesn't fit the outline (for example "1 days") into its own named test. It SHALL list every wording change in its report for the author to confirm.

#### Scenario: Review does not edit
- **WHEN** the user asks to review `tests/` for BDD quality
- **THEN** the agent reports findings with check IDs and changes no file

#### Scenario: Wording changes are listed
- **WHEN** pasted Gherkin has an outline row whose sentence reads "1 days"
- **THEN** that row becomes its own named test, and the report lists the change

### Requirement: Native Robot Framework only

The skill SHALL produce only `.robot`, `.resource`, Python library and data files that standard Robot Framework runs. It SHALL NOT create `.feature` files, configure a Gherkin parser, or use constructs that need a parser or plugin outside Robot Framework and the project's own libraries. DataDriver MAY be used for external data sets when the project has it installed or the user asks for it, with its install delegated to `rf-setup`.

#### Scenario: Pasted feature file becomes a suite
- **WHEN** the user pastes a Gherkin feature with a Background, two Rules and a Scenario Outline
- **THEN** the result is `.robot` suites (a feature directory with `__init__.robot` when there are several files), and no `.feature` file or parser configuration exists in the project

### Requirement: Robocop asset matches the default style

`assets/robocop-bdd.toml` SHALL configure, for both the pinned Robocop version and Robocop 9.x:
- NAME02 and NAME18 to `first_word_capitalized`, with a pattern that accepts possessive `'s`;
- VAR06 ignored for `*_steps.resource`;
- template alignment that keeps test names next to their rows;
- a separator rule that skips keyword calls starting with a BDD prefix.

`references/robocop.md` SHALL explain how to merge these settings into an existing `robot.toml` or `pyproject.toml`. It SHALL say that the nearest configuration file wins, and that multiple rules are selected by repeating `--select`.

#### Scenario: Examples lint clean with the asset
- **WHEN** `robocop check` runs with the asset's settings on the resource-strategy example
- **THEN** it reports no NAME02, NAME18 or VAR06 finding

### Requirement: Runnable, library-neutral examples

`assets/examples/` SHALL contain:
- a fake system under test in Python;
- a resource-strategy project, with `robot.toml`, a feature directory with `__init__.robot`, a scenarios file and an outline file, and a steps resource;
- a World-library project, with `robot.toml`, a `@library(scope="TEST")` World library and one suite.

The examples SHALL call only BuiltIn and standard-library keywords and keywords of their own libraries and resources. Every `robotframework` code block in `SKILL.md` and the references SHALL either be extracted from an example file or pass a dry run against a copy of the examples. A block whose first line starts with `# Wrong` is a counter-example and is excluded.

#### Scenario: Examples run
- **WHEN** `plugins/rf-core/tests/test_bdd_skill.py` runs with Robot Framework installed
- **THEN** both example projects pass `robotcode analyze code`, a dry run and a real run

#### Scenario: Code blocks are valid
- **WHEN** the test extracts the `robotframework` code blocks from `SKILL.md` and the references
- **THEN** every block that isn't a counter-example passes a dry run

### Requirement: Gotchas state the verified BDD traps

The `Gotchas` section SHALL contain at least these items, each with behaviour, cause and what to write instead:
1. a step keyword defined with a prefix cannot be called with another prefix;
2. a passing dry run doesn't prove that a step matched the intended keyword, so a real run is needed;
3. adjacent embedded arguments in a step need quotes or patterns;
4. literal text in a step name is matched exactly (`day(s)` is not optional text);
5. an outline sentence that doesn't fit every row needs its own test, not an `IF` in the template keyword;
6. mutating a declared `@{EMPTY}`/`&{EMPTY}` container leaks state into later tests, so rebuild it with `VAR … scope=TEST`;
7. a `Test Setup` in `__init__.robot` needs the steps resource imported in every child suite;
8. Robocop reads only the nearest configuration file, so the BDD settings go into the file the project uses;
9. a comma-separated `--select` selects nothing;
10. `tag-doc` and `tag-stat-link` patterns use `?` instead of `:`;
11. DataDriver needs a template keyword with normal `[Arguments]`, and discovery sees only its placeholder test.

Every trap SHALL be verified against the pinned Robot Framework, robotcode and Robocop versions before it is published.

#### Scenario: Minimum gotchas present
- **WHEN** the structure test parses the `Gotchas` section
- **THEN** it finds at least 11 list items, including items that mention dry run, `IF`, `scope=TEST`, `__init__.robot`, `--select` and DataDriver

### Requirement: Companion Skills integration for rf-bdd

`SKILL.md` SHALL end with a `## Companion Skills` `Need | Skill` table with rows for `rf-language`, `rf-setup` and `rf-python-library`, using the shared catalogue wording. A sentence after the table SHALL name the robotcode plugin's `robotcode` skill. The shared catalogue SHALL gain a `bdd` key, with the Need "Write or review BDD (Given/When/Then) specifications and their step keywords", and `rf-language`'s table SHALL contain that row.

#### Scenario: Rows present
- **WHEN** `tests/test_skill_descriptions.py` parses the Companion Skills tables
- **THEN** rf-bdd has the `language`, `setup` and `python-library` rows, and rf-language has the `bdd` row

### Requirement: Trigger query set for rf-bdd

`plugins/rf-core/evals/triggers/rf-bdd.yaml` SHALL contain at least 8 should-trigger and 8 should-not-trigger queries. Both polarities SHALL appear in the train and validation splits. Should-not-trigger queries SHALL include:
- plain Robot Framework syntax tasks that belong to `rf-language`;
- a Python library task;
- a robotcode results task;
- Cucumber step definitions in Java;
- pytest-bdd.

`rf-language` loading alongside `rf-bdd` on a BDD query SHALL NOT count as a failure of either set. The description SHALL meet the trigger-accuracy acceptance rules of the skill-triggering spec on the validation split.

#### Scenario: Set loads
- **WHEN** the trigger-set loader test runs
- **THEN** `rf-bdd.yaml` passes the shape rules, and no query names a skill id

#### Scenario: Accuracy gate
- **WHEN** the trigger evaluation runs on the validation split under the default listing budget
- **THEN** should-trigger recall is at least 0.80 and should-not-trigger accuracy is at least 0.90, or the shortfall is recorded under rule (b)

### Requirement: Eval tasks show the skill helps

`plugins/rf-core/evals/tasks/` SHALL contain rf-bdd tasks on fixture `sut-bdd-library`:
- at least three narrow tasks: greenfield feature, outline with a template, extending an existing vocabulary;
- at least one adversarial task: pasted Gherkin with a row that doesn't fit the outline;
- one review task with seeded issues, graded on no edits and on the reported check IDs.

Gating checks SHALL be deterministic: tests pass with an expected count, only BDD-prefixed calls or template rows in test bodies, suite documentation and feature metadata or tags present, no `.feature` file, and no edits in the review task. Baselines SHALL be stored for the current CI model.

#### Scenario: Tasks load and gate
- **WHEN** `rf-skill-eval` lists the tasks for plugin `rf-core`
- **THEN** the rf-bdd tasks load, each names `skill: rf-bdd` and fixture `sut-bdd-library`, and each has at least one gating deterministic check

#### Scenario: Baselines recorded
- **WHEN** the change is complete
- **THEN** `plugins/rf-core/evals/baselines/` contains results for the rf-bdd tasks and trigger set on the current CI model
