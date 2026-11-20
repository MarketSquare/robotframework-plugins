# Gherkin Concepts in Robot Framework

- [Overview](#overview)
- [Feature](#feature)
- [Rule](#rule)
- [Background](#background)
- [Scenario and steps](#scenario-and-steps)
- [Scenario Outline and Examples](#scenario-outline-and-examples)
- [Step arguments](#step-arguments)
- [Constructs without a Robot Framework form](#constructs-without-a-robot-framework-form)
- [Translating pasted Gherkin](#translating-pasted-gherkin)

Robot Framework has a native form for almost every Gherkin concept, so a BDD suite needs no Gherkin parser and no `.feature` file. A reader who knows Gherkin recognises every part, and robotcode still checks every line. Code blocks run in a copy of `assets/examples/resource-strategy/`.

## Overview

| Gherkin | Robot Framework form |
|---|---|
| `Feature:` with a user story | one suite file: the story in `Documentation`, `Metadata    Feature    <name>`, `Test Tags    feature:<slug>` |
| a feature with a Scenario Outline | a feature directory: `__init__.robot` holds the story, metadata, feature tag and Background; one file holds the scenarios; one file per outline |
| a group of features | a directory whose `__init__.robot` has a `Documentation` |
| `Rule:` | `[Documentation]    Rule: …` on the test, plus a `rule:<slug>` tag |
| `Background:` | `Test Setup    Given <one sentence>`, when two or more tests share it |
| `Scenario:` / `Example:` | a test whose name states the behaviour |
| `Given` / `When` / `Then` / `And` / `But` | the same words as prefixes on step calls |
| a step parameter | an embedded argument: `"${reason}"`, `${amount: int}` |
| `Scenario Outline:` with `Examples:` | `Test Template`, one named test per row, column labels in the `*** Test Cases ***` header |
| a data table | arguments after the step: `key=value` pairs or a list |
| a doc string `"""` | continuation lines passed as `@{lines}` |
| `@tag` | `Test Tags` for the file, `[Tags]` for one test |
| `# language: de` | `Language: German` as the first line, with localised prefixes |
| `Before` / `After` hooks | `Suite Setup`, `Suite Teardown`, `Test Teardown` with technical keywords only |

## Feature

A feature with only ordinary scenarios is one file, named after the feature in snake case. Each test documents its rule.

<!-- file: tests/overdraft_protection.robot -->
```robotframework
*** Settings ***
Documentation       As an account holder
...                 I want the ATM to refuse withdrawals above my balance
...                 So that my account is never overdrawn by accident
Metadata            Feature    Overdraft protection
Resource            cash_withdrawal_steps.resource
Test Setup          Given the ATM holds 500 EUR
Test Tags           feature:overdraft-protection


*** Test Cases ***
Withdrawal above the balance is refused
    [Documentation]    Rule: an account cannot be overdrawn at the ATM.
    [Tags]    rule:no-overdraft
    Given Alice has a balance of 10 EUR
    When Alice withdraws 20 EUR
    Then the withdrawal is refused with "Insufficient funds"
    And Alice's balance is 10 EUR

Withdrawal of the whole balance is dispensed
    [Documentation]    Rule: a withdrawal up to the balance is dispensed and debited.
    [Tags]    rule:debit-on-dispense
    Given Alice has a balance of 100 EUR
    When Alice withdraws 100 EUR
    Then the ATM dispenses 100 EUR
    And Alice's balance is 0 EUR
```

- The story lines appear at the top of the report and the log. `Metadata    Feature` lists the feature in the suite metadata, and the `feature:` tag lets people run the feature alone.
- A feature that also has an outline becomes a directory. `assets/examples/resource-strategy/tests/cash_withdrawal/` shows the layout: `__init__.robot`, `withdrawal_rules.robot` and `remaining_balance.robot`.
- What an `__init__.robot` may contain, and what child suites inherit from it: see the `rf-language` skill.

## Rule

Robot Framework has no rule block. Put the rule in the test's `[Documentation]`, starting with `Rule:`, and tag the test `rule:<slug>`:
- The documentation keeps the rule next to its examples in the report.
- The tag runs one rule alone (`--include rule:no-overdraft`) and gives each rule a pass/fail row in the tag statistics.
- When every test in a file has the same rule, move the tag to `Test Tags` (Robocop TAG05 suggests it) and keep the `Rule:` line in each test. `assets/examples/resource-strategy/tests/daily_withdrawal_limit.robot` does this.

## Background

A Background is `Test Setup` with one `Given` sentence: `Test Setup    Given the ATM holds 500 EUR`.
- Use it only for a starting state that two or more tests in the file share. Otherwise it stays in the test as the first `Given`.
- A setup is one keyword. When the shared state has several facts, name the whole state in one sentence (`Given a fully loaded ATM with a daily limit of 300 EUR`) and document what it sets up. Don't chain steps with `Run Keywords … AND …`.
- In a feature directory, `Test Setup` in `__init__.robot` applies to every test of the feature. Every child suite must import the steps resource that defines it.
- Never put business state in `Suite Setup`: the tests would share it. `Suite Setup` is for technical setup, such as starting the application.

## Scenario and steps

- The test name states the behaviour: "Withdrawal above the balance is refused", not "Test withdrawal 2".
- The body holds only prefixed steps, in the order Given, When, Then, with one `When`. `And` continues the previous phase; `But` adds a contrasting outcome (`But no fee is charged`).
- Robot Framework drops the prefix before it looks up the keyword, so one step keyword can serve as `Given` in one test and `Then` in another. Give it a sentence that reads well in both places, or define two sentences.

## Scenario Outline and Examples

An outline is a file of its own with `Test Template`, and each example row is a named test. The `*** Test Cases ***` header labels the columns, so the file reads like an Examples table. The runnable outline is `assets/examples/resource-strategy/tests/cash_withdrawal/remaining_balance.robot`.

- The template keyword is the outline sentence. Its body holds the Given/When/Then steps, and it stays in the outline file.
- Name every example after what makes it different ("Withdrawal of the whole balance"). Don't put `${variables}` in example names; robotcode shows a `VariableNotReplaced` hint.
- The outline sentence must read correctly for every row. A row that needs other words ("on the due date" instead of "0 days late") becomes its own named test in the scenarios file, not an `IF` in the template keyword.
- Keep ordinary scenarios out of the outline file, because `Test Template` applies to every test in it.
- Template mechanics, row forms and status rules: see the `rf-language` skill.

## Step arguments

Gherkin data tables and doc strings become arguments after the step, on continuation lines when they are long:

| Data | Step call | Keyword arguments |
|---|---|---|
| key and value (holder and balance) | `Given the following accounts exist    Alice=100    Bob=500` | `[Arguments]    &{balances}` |
| a list of values | `Then the menu offers    Withdraw cash    Check balance` | `[Arguments]    @{entries}` |
| multi-line text (a receipt, a message) | `Then the receipt reads` with `...    <line>` rows | `[Arguments]    @{lines}`, joined in the step |

The calls, with the steps resource below:

```text
Given the following accounts exist    Alice=100    Bob=500
When Alice withdraws 20 EUR
Then the receipt reads
...    Withdrawal: 20 EUR
...    Balance: 80 EUR
```

<!-- file: resources/branch_steps.resource -->
```robotframework
*** Settings ***
Documentation       Step definitions for accounts and receipts.
Library             AtmService


*** Keywords ***
The following accounts exist
    [Documentation]    Opens one account per ``holder=balance`` pair (balances in EUR).
    [Arguments]    &{balances}
    FOR    ${holder}    ${balance}    IN    &{balances}
        Open Account    ${holder}    ${balance}
    END

The receipt reads
    [Documentation]    The last receipt has exactly these ``lines``, in order.
    [Arguments]    @{lines}
    ${expected}    Catenate    SEPARATOR=\n    @{lines}
    ${receipt}    Get Last Receipt
    Should Be Equal    ${receipt}    ${expected}
```

- `key=value` pairs suit items with one attribute each. The sentence says what the key and the value are, and `[Documentation]` gives the unit.
- When an item has several attributes, don't invent a table format. Write one step per fact, or name the starting state.
- Many rows of values for the same behaviour are an outline, not a table.
- For structured payloads, compare parsed fields (`The account summary contains    holder=Alice    balance=80`) instead of raw JSON text.

## Constructs without a Robot Framework form

| Gherkin | Write instead |
|---|---|
| `Or` steps | separate tests, or an outline |
| a step that calls another step | a technical keyword that both steps call |
| hooks with business meaning | a visible `Given` step or a Background |
| a header row on Examples | the `*** Test Cases ***` header of the outline file |
| feature description paragraphs | more lines in the suite `Documentation`, after the story |
| a step table with several columns | one step per fact, a named starting state, or an outline |
| `.feature` files | `.robot` suites built with this mapping; no Gherkin parser |

## Translating pasted Gherkin

Translate the meaning, not the exact words. Keep every rule and every example, apply the house rules, and list each wording change in the report so the author can confirm it.

```gherkin
Feature: Late returns
  Background:
    Given the library charges 0.50 EUR per day late

  Rule: each late day costs a fee
    Scenario Outline: Fee for a late return
      When Alice returns a book <days> days late
      Then Alice pays <fee> EUR
      Examples:
        | days | fee  |
        | 0    | 0.00 |
        | 1    | 0.50 |
        | 3    | 1.50 |
        | 5    | 2.50 |
```

The result is a feature directory, because the feature has an outline:

```text
tests/late_returns/__init__.robot    story, Metadata Feature, feature:late-returns, Test Setup (the Background)
tests/late_returns/return_fees.robot
    Book returned on the due date costs nothing          (row days=0)
    Book returned one day late costs 0.50 EUR            (row days=1)
tests/late_returns/late_fee.robot    Test Template: Returning a book ${days} days late costs ${fee} EUR
    Three days late                                      (row days=3)
    Five days late                                       (row days=5)
```

Wording changes for the report:
- Row `0`: "0 days late" reads wrong, so it became the named test "Book returned on the due date costs nothing".
- Row `1`: "1 days late" reads wrong, so it became the named test "Book returned one day late costs 0.50 EUR".
- `When … Then …` became one template sentence, `Returning a book ${days} days late costs ${fee} EUR`, for the rows that fit it.
- Also list split conjunction steps ("has a card and 100 EUR"), vague outcomes made concrete ("it works"), and placeholder data replaced with realistic values.
