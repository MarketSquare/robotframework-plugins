# Data-Driven Specifications

- [The ladder](#the-ladder)
- [Named examples with Test Template](#named-examples-with-test-template)
- [One rule, many inputs: [Template] in one test](#one-rule-many-inputs-template-in-one-test)
- [Values after a step](#values-after-a-step)
- [External data files: DataDriver](#external-data-files-datadriver)
- [Smells](#smells)

The same behaviour checked with several inputs is a Scenario Outline in Gherkin. Robot Framework offers templates with named rows, arguments after a step, and external data through DataDriver. Pick the simplest form that keeps the specification readable. Code blocks run in a copy of `assets/examples/resource-strategy/`.

## The ladder

| Situation | Form |
|---|---|
| a few examples of one behaviour, each worth a name | an outline file with `Test Template`, one named test per row |
| one rule, many inputs that behave the same and need no names | `[Template]` on one test, one row per input |
| one step needs a set of values | arguments after the step: `key=value` pairs or a list |
| the examples live in a CSV or Excel file the user names, or business people maintain them there | DataDriver with a normal-argument template |

Start at the top. Move down only when the situation calls for it.

## Named examples with Test Template

This is the standard outline: one file per outline, column labels in the `*** Test Cases ***` header, and each row a named test. The runnable file is `assets/examples/resource-strategy/tests/cash_withdrawal/remaining_balance.robot`.

- The template keyword has embedded arguments, so the log shows each example as a sentence ("Withdrawing 20 EUR from a balance of 100 EUR leaves 80 EUR") with its steps under it.
- Each row is its own test, so the report has one line per example and one example can be run alone by its longname.
- The outline sentence must fit every row. "Returning a book 1 days late" or "0 days late" means one sentence is stretched over examples that read differently. Give such a row its own named test with its own sentence ("Book returned on the due date costs nothing") in the feature's scenarios file, and keep the outline for the rows that share one sentence.
- Never branch on the input with `IF` in a template keyword, and never put alternative wording such as `day(s)` in the name; literal text is matched exactly. Both hide several behaviours in one outline.
- Template mechanics (row forms, `[Template]    NONE`, settings per row) and status rules: see the `rf-language` skill.

## One rule, many inputs: [Template] in one test

When a rule has many inputs that behave the same way, and naming each would add nothing, use one test named after the rule, with `[Template]` and one row per input:

<!-- file: tests/withdrawal_amounts.robot -->
```robotframework
*** Settings ***
Documentation       As a bank
...                 I want the ATM to accept only amounts it can dispense in notes
...                 So that account holders never ask for coins it does not have
Metadata            Feature    Withdrawal amounts
Resource            cash_withdrawal_steps.resource
Test Tags           feature:withdrawal-amounts    rule:multiples-of-ten


*** Test Cases ***
Amounts that are not a multiple of 10 EUR are refused
    [Documentation]    Rule: the ATM only dispenses multiples of 10 EUR.
    [Template]    A withdrawal of ${amount} EUR is refused as not a multiple of 10 EUR
    5
    15
    99


*** Keywords ***
A withdrawal of ${amount} EUR is refused as not a multiple of 10 EUR
    [Documentation]    One input for the multiples-of-ten rule.
    Given Alice has a balance of 1000 EUR
    When Alice withdraws ${amount} EUR
    Then the withdrawal is refused with "Amount must be a multiple of 10 EUR"
    And Alice's balance is 1000 EUR
```

- Each row is a full scenario, Given to Then, so the rows don't affect each other.
- Keep the rows to one screen. When rows need comments to explain them, they deserve names: switch to a `Test Template` outline.

## Values after a step

When one step, not the whole scenario, needs several values, pass them on continuation lines:

| Shape | Call | Keyword |
|---|---|---|
| key and value | `Given the ATM holds these notes    20=40    50=10` | `[Arguments]    &{notes}` |
| list | `Then the menu offers    Withdraw cash    Check balance` | `[Arguments]    @{entries}` |

An item with several attributes gets one step per fact, or a named starting state. Many rows of values for the same behaviour are an outline.

## External data files: DataDriver

DataDriver (`robotframework-datadriver`) generates one test per row of a CSV, Excel or JSON file at run time. Use it only when the user names an external data file, or when non-programmers maintain the examples in a spreadsheet. Otherwise the examples belong in the `.robot` file, next to the rule. Installing it is a job for the `rf-setup` skill. The blocks below are marked as text because they need DataDriver to run.

```text
*** Settings ***
Documentation       As a product owner
...                 I want to maintain withdrawal examples in a spreadsheet
...                 So that the business can add cases without editing tests
...
...                 Examples: withdrawal_examples.csv
Metadata            Feature    Withdrawal examples
Resource            cash_withdrawal_steps.resource
Library             DataDriver    file=withdrawal_examples.csv
Test Tags           feature:withdrawal-examples    rule:debit-on-dispense
Test Template       Withdrawal leaves the remaining balance


*** Test Cases ***
Withdrawal example    0    0    0


*** Keywords ***
Withdrawal leaves the remaining balance
    [Documentation]    One row of withdrawal_examples.csv.
    [Arguments]    ${amount}    ${balance}    ${rest}
    Given Alice has a balance of ${balance} EUR
    When Alice withdraws ${amount} EUR
    Then the ATM dispenses ${amount} EUR
    And Alice's balance is ${rest} EUR
```

`tests/withdrawal_examples.csv`:

```text
*** Test Cases ***;${amount};${balance};${rest};[Tags];[Documentation]
Partial withdrawal;20;100;80;;Leaves most of the balance
Withdrawal of the whole balance;100;100;0;boundary;Leaves nothing
Withdrawal of a single note;10;250;240;;
```

How it differs from a native template (checked with DataDriver 1.11.2):
- The template keyword needs normal `[Arguments]`, not embedded arguments. DataDriver passes the columns by name. An embedded-argument template passes the dry run and then fails every row with `Variable '${amount}' not found`. The steps inside still read as sentences.
- The default CSV dialect is `Excel-EU`, so the separator is `;`. The first header is `*** Test Cases ***` and holds the test names; `[Tags]` and `[Documentation]` columns are optional. A comma-separated file fails with an "Unassigned … argument detected" error from DataDriver.
- The placeholder test (`Withdrawal example    0    0    0`) is replaced at run time. Keep `${variables}` out of its name.
- `robotcode discover` and editor test explorers see only the placeholder. The dry run and the real run see the generated tests. Tell the user.
- Robot Framework selects tests before DataDriver generates them, so `--test "Partial withdrawal"` and `--include boundary` find nothing. Run the whole suite, and pick one row with `--variable "DYNAMICTEST:Withdrawal Examples.Partial withdrawal"`, or filter rows with DataDriver's `include=` and `exclude=` library arguments.
- Readability moves to the data file. Review the CSV like a specification: realistic names, no placeholder data, one behaviour.

## Smells

| Smell | What it usually means |
|---|---|
| 20 or more rows in an outline | a pure data test; keep representative examples and move exhaustive checks to unit tests |
| rows that need comments | the rows test different rules; split by rule and name the rows |
| `IF` on the input in a template keyword | several behaviours in one outline; write one outline per behaviour |
| columns like `expected_status_code` or `sql_result` | implementation details in the specification |
| DataDriver for three examples | an inline `Test Template` is easier to read, and the tools see it |
