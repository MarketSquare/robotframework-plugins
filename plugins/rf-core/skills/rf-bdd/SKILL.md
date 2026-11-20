---
name: rf-bdd
description: "Use for BDD in Robot Framework: Given/When/Then specs, step vocabularies, Gherkin or acceptance criteria to .robot, reviews."
license: Apache-2.0
compatibility: "Requires Python 3.8+ with robotframework>=7 and robotcode[all]>=2.8 (which includes Robocop) in the project environment; the examples need RF 7.3+."
metadata:
  author: manykarim
---

# Robot Framework BDD

Write and review behaviour-driven specifications in native `.robot` and `.resource` files: features, rules and examples as suites, documentation and tags, one step vocabulary, and scenario state in a declared place.
Robot Framework syntax (embedded arguments, templates, tags, imports) comes from `rf-language`; load both.
Verified against Robot Framework 7.4.2.

## When to use

Load this skill together with `rf-language` when tests are written or reviewed as a specification:

- "BDD style", "Given/When/Then", "executable specification", "specification by example", acceptance tests;
- acceptance criteria, user stories or Gherkin (Cucumber, a `.feature` text) pasted as input for Robot Framework tests;
- a scenario outline or Examples table, a Background, rules and features;
- reviewing the readability or consistency of tests or step keywords, or a step vocabulary that drifts.

Not this skill: plain Robot Framework syntax, keyword-driven or data-driven tests without a specification, resources and variables use `rf-language`; `rf-bdd` relies on `rf-language` for syntax details. Running, discovery, keyword lookup and result reading are covered by the `robotcode` skill of the robotcode plugin.

## Version gate

Establish the project's Robot Framework version before writing version-dependent syntax (`rf-language` shows how).

| Feature | Min RF | On older versions |
|---|---|---|
| `VAR … scope=TEST` | 7.0 | `Set Test Variable` |
| BDD prefix before a leading embedded argument (`Given ${holder} has …`) | 7.1 | start the step with literal text |
| Typed embedded arguments `${amount: int}`, typed `[Arguments]` | 7.3 | `${amount:\d+}` and `Convert To Integer` |
| Test-level `[Metadata]` | 7.5 | suite `Metadata` or `[Documentation]` |

The examples in `assets/examples/` need RF 7.3. They use suite `Metadata` only.

## Step 0: Match the project

Detect the project's conventions before writing, and follow them. Use `rf-language`'s Step 0 (its conventions report lists the BDD steps, templates and tags), or search:

```bash
grep -rhoE '^\s+(Given|When|Then|And|But) .*' tests | head -20
grep -rlE '^\*\*\* Keywords \*\*\*' --include='*.resource' .
grep -rhE '^(Resource|Library)\s' tests | sort | uniq -c
grep -nE 'robocop|python-path' robot.toml pyproject.toml 2>/dev/null
```

Follow what you find:

- **Step casing.** Title Case steps (`The Cart Contains ${count} Items`) stay Title Case. Leave the project's Robocop configuration alone.
- **Imports.** By name with the folder on `python-path`, or relative paths, as the project does.
- **State.** Variables in a steps resource, or a World library in Python.
- **Vocabulary.** `robotcode doc keywords <steps resource or library>` lists the existing sentences.
- **Tags.** `robotcode discover tags` lists the tags in use.

Only when the project has no convention for an item, use the default:

- sentence-style step names with only the first word capitalized, plus the settings of `assets/robocop-bdd.toml` merged into the project's Robocop configuration;
- imports by name, with the folder on `python-path` in `robot.toml`;
- the resource strategy for state.

## House rules

Every suite has this shape (the steps are defined in `assets/examples/resource-strategy/resources/cash_withdrawal_steps.resource`):

```robotframework
*** Settings ***
Documentation       As an account holder
...                 I want to withdraw cash from an ATM
...                 So that I can get money when the bank is closed
Metadata            Feature    Cash withdrawal
Resource            cash_withdrawal_steps.resource
Test Setup          Given the ATM holds 500 EUR
Test Tags           feature:cash-withdrawal


*** Test Cases ***
Withdrawal above the balance is refused
    [Documentation]    Rule: an account cannot be overdrawn at the ATM.
    [Tags]    rule:no-overdraft
    Given Alice has a balance of 10 EUR
    When Alice withdraws 20 EUR
    Then the withdrawal is refused with "Insufficient funds"
    And Alice's balance is 10 EUR
```

1. **Three layers.** Test bodies hold only `Given`/`When`/`Then`/`And`/`But` steps or template rows. A step keyword states one domain sentence and calls domain keywords, which call technical keywords (UI, API, database). Tag helpers in a steps resource `robot:private`, so robotcode warns when a test calls them. *Why:* a business reader can read the test, and a UI change touches one layer.
2. **One behaviour per test.** Given, one `When`, then Then, in fewer than 10 steps. The test name states the behaviour, not the procedure. *Why:* a failure names one broken rule.
3. **Domain language.** Third person, present tense, one idea per step, concrete data (`Alice`, `100 EUR`), no locators, URLs, HTTP verbs or SQL. A `Then` names an observable outcome. *Why:* the specification outlives the implementation.
4. **Step naming.** Casing from Step 0. Values are embedded arguments, strings in quotes (`"${reason}"`), numbers typed or restricted by a pattern. Every step keyword has `[Documentation]`. *Why:* quotes and patterns keep steps from matching each other.
5. **One vocabulary.** List the existing steps before writing one, and reuse or extend them. Never add a synonym ("logged in" next to "signed in"). *Why:* two sentences for one fact drift apart.
6. **Gherkin mapping.** Feature → suite, or a feature directory with `__init__.robot`. Rule → `[Documentation]    Rule: …` plus a `rule:<slug>` tag. Background → `Test Setup    Given …`, shared by two or more tests. Outline → `Test Template` with named rows, only when one sentence fits every row; never an `IF` in the template keyword. *Why:* Robot Framework has a native form for every concept.
7. **State in the declared place.** Declare each state variable in the steps resource's `*** Variables ***` and assign it with `VAR … scope=TEST`, or keep it in a World library with `@library(scope="TEST")`. Never change a declared list or dictionary in place. *Why:* in-place changes leak into the next test.
8. **Independent tests.** No test relies on another test's data or order. Business state never goes into `Suite Setup`. *Why:* tests run alone, in any order, and in parallel.
9. **Living documentation.** The suite has the user story in `Documentation`, `Metadata    Feature    <name>` and a `feature:<slug>` tag; rules and step keywords are documented. *Why:* the log and report read as the specification.
10. **Imports by the project's convention.** By default import by name (`Resource    cash_withdrawal_steps.resource`) with the folder on `python-path`. *Why:* names don't break when files move.
11. **Style tooling.** Check style with Robocop using the project's configuration; in a new project, add `assets/robocop-bdd.toml`. Write assignments without `=` (`${balance}    Get Balance    ${holder}`). *Why:* the hook and CI lint with the same rules.

## Write a specification

1. **Understand the behaviour.** Write down who benefits and why, the rules, and for each rule a normal case, a boundary and a refusal. Ask about any open question that would change a rule; mark other inferences as assumptions.
2. **Discover the project** (Step 0): suites and tags with `robotcode discover suites` and `robotcode discover tags`, the vocabulary with `robotcode doc keywords`, the state strategy and the Robocop configuration.
3. **Draft the scenarios as sentences** before writing any keyword. Fix wording that needs explaining or names UI details.
4. **Choose the layout.** One feature without an outline → `<feature>.robot`. A feature with an outline → a directory with `__init__.robot` (story, `Metadata`, feature tag, shared `Test Setup`), a rules file and one file per outline. Many examples of one behaviour → `references/data-driven.md`.
5. **Write the steps,** reusing sentences first, then domain and technical keywords below them. Each `Then` asserts with a message a reader understands.
6. **Validate** and fix before moving on:
   1. `robotcode analyze code <changed files>`: no errors. A `VariableNotFound` on state means the variable isn't declared.
   2. `robotcode robot --dryrun -bl "<longname>"`: every step resolves.
   3. `robotcode robot -bl "<longname>"`: the tests pass. If the system under test isn't reachable, say so.
   4. `robocop check --no-cache <changed files>`: no findings with the project's configuration.
7. **Report** the rules and their tests, the files touched, the validation results, assumptions and open questions, and any convention you followed or added.

## Review a specification

1. Gather evidence: `robotcode analyze code`, `robotcode discover tags`, `robotcode doc keywords` on the steps resources and libraries, and `robocop check --no-cache <paths>`.
2. Read every test and step against `references/review-checklist.md`.
3. Report findings by severity, one per line in the format `ID — file:line — problem — rewrite`.
4. Don't edit files in review mode. Change them only when the user asks, then validate as in Write.

## Gherkin input

Pasted Gherkin or acceptance criteria become native `.robot` suites (mapping: `references/gherkin-mapping.md`). Don't create `.feature` files and don't install or configure a Gherkin parser; say so in one sentence.

- Translate the meaning, not the exact wording. Keep every rule and every example.
- An Examples row whose sentence doesn't fit the outline ("1 days") becomes its own named test (`Returning a book one day late costs 0.50 EUR`).
- Split steps joined with "and", and make vague outcomes concrete.
- List every wording change in the report, so the author can confirm it.

## Gotchas

- A step keyword defined with a prefix (`Given the app is open`) cannot be called as `When the app is open`. Define steps without a prefix.
- A passing dry run doesn't prove that a step matched the keyword you meant: an embedded pattern can bind another keyword or the wrong values. Run the affected tests for real by longname.
- Adjacent embedded arguments (`${holder} ${amount} EUR`) split at an unexpected place. Separate them with literal text, quote strings (`"${reason}"`) or add a pattern (`${amount:\d+}`).
- Literal text in a step name is matched exactly: `day(s)` is not optional text, so `1 day` doesn't match `${n} day(s)`. Write one sentence per form.
- An outline sentence that doesn't fit every row ("1 days late") needs its own named test. An `IF` in the template keyword hides a second behaviour.
- Changing a declared `@{EMPTY}` or `&{EMPTY}` container in place (`Append To List`, `Set To Dictionary`) leaks into later tests. Rebuild it with `VAR    @{ITEMS}    @{ITEMS}    new    scope=TEST`.
- A `Test Setup` in `__init__.robot` calls the step with the child suite's imports, so every child suite imports the steps resource. `robotcode analyze code` doesn't report a missing import; the dry run fails with `No keyword with name 'Given …' found`.
- Robocop reads only the nearest configuration file. Put the BDD settings into the file the project already uses for Robocop.
- A comma-separated `--select` selects nothing; repeat `--select` for each rule.
- `tag-doc` and `tag-stat-link` patterns write `?` for the `:` in tags such as `feature:cash-withdrawal`.
- DataDriver needs a template keyword with normal `[Arguments]`: an embedded-argument template passes the dry run, then fails every row with `Variable '${amount}' not found`. `robotcode discover` and editors show only the placeholder test, so select a row with `--variable "DYNAMICTEST:<suite>.<row name>"`, not `--test`.

## When to read the references

| Reference | Read when |
|---|---|
| `references/gherkin-mapping.md` | Translating Gherkin or acceptance criteria: features, rules, backgrounds, outlines, step arguments |
| `references/step-design.md` | Writing or naming step keywords, embedded arguments in steps, reusing a vocabulary |
| `references/state.md` | Passing data between steps: the resource strategy or a World library |
| `references/data-driven.md` | Many examples of one behaviour: templates, `[Template]`, DataDriver |
| `references/documentation-and-tags.md` | Suite and test documentation, `Metadata`, feature and rule tags, localised specifications |
| `references/robocop.md` | Adding or merging the Robocop settings of `assets/robocop-bdd.toml` |
| `references/review-checklist.md` | Reviewing a specification: check IDs, severities and the findings format |

`assets/examples/` holds a fake ATM service (`sut/`) and two runnable projects: `resource-strategy/` (the default) and `world-strategy/` (a World library).

## Companion Skills

| Need | Skill |
|------|-------|
| Write tests, suites, user keywords, resources and variables in Robot Framework syntax | `rf-language` |
| Install Robot Framework or a library, fix the environment | `rf-setup` |
| Write or fix a Python keyword library or listener | `rf-python-library` |

For running, discovering, keyword documentation, result analysis and debugging with the robotcode CLI, use the `robotcode` skill of the robotcode plugin (`robotcode@robotframework-agent-plugins`).
