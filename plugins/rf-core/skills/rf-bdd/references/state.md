# Scenario State

- [Choose the strategy](#choose-the-strategy)
- [Resource strategy](#resource-strategy)
- [The leak: never mutate a declared container](#the-leak-never-mutate-a-declared-container)
- [World-library strategy](#world-library-strategy)
- [What not to do](#what-not-to-do)

A `When` step produces a result that a later `Then` step checks, so steps share state. Robot Framework has two clean places for it: variables declared in the steps resource, or a Python World library with test scope. Code blocks run in a copy of `assets/examples/resource-strategy/`.

## Choose the strategy

1. The project has step keywords in a Python library (`@keyword("…${arg}…")`): use the World-library strategy for that domain.
2. The project has `*_steps.resource` files: use the resource strategy.
3. A new project, or a new domain with no convention: use the resource strategy.
4. Don't mix the two strategies within one domain.

## Resource strategy

The steps resource declares every state variable in `*** Variables ***` with a neutral default, and steps assign it with `VAR … scope=TEST` (Robot Framework 7.0+). `assets/examples/resource-strategy/resources/cash_withdrawal_steps.resource` declares `${LAST_WITHDRAWAL}    ${None}`; `${holder} withdraws ${amount: int} EUR` assigns it, and the `Then` steps read it.

- Declare every state variable, with `${None}`, `@{EMPTY}` or `&{EMPTY}` as the default. Without the declaration, `robotcode analyze code` reports `VariableNotFound` on every step that reads it. Robocop VAR01 rejects an empty declaration.
- `scope=TEST` keeps the value for one scenario. The next test starts from the declared default.
- Upper-case names mark shared state; local variables stay lower case.
- The Robocop asset turns off VAR06 for `*_steps.resource` files only, because test-scope state is the design there.
- Often the best state is the system under test itself: `${holder}'s balance is …` asks the ATM. Keep variables for what the system doesn't keep for you, such as the result of the last action.

## The leak: never mutate a declared container

A declared list or dictionary is one object, shared by every test in the suite. Changing it in place with `Set To Dictionary`, `Append To List` or `Remove From Dictionary` changes the default, and the next test sees the leftovers.

```robotframework
# Wrong: the next test in the suite still sees these notes.
*** Keywords ***
The ATM holds ${count: int} notes of ${value: int} EUR
    [Documentation]    Leaks into the next test.
    Set To Dictionary    ${NOTES}    ${value}    ${count}
```

Build a new value and assign it with `VAR … scope=TEST`:

<!-- file: resources/note_steps.resource -->
```robotframework
*** Settings ***
Documentation       Step definitions for loading notes into the ATM.


*** Variables ***
&{NOTES}            &{EMPTY}


*** Keywords ***
The ATM holds ${count: int} notes of ${value: int} EUR
    [Documentation]    Adds ``count`` notes of ``value`` euros to the ATM's cassettes.
    VAR    &{NOTES}    &{NOTES}    ${value}=${count}    scope=TEST

The notes in the ATM add up to ${total: int} EUR
    [Documentation]    The value of all loaded notes is exactly ``total`` euros.
    ${sum}    Evaluate    sum(int(value) * count for value, count in $NOTES.items())
    Should Be Equal    ${sum}    ${total}
    ...    msg=The notes add up to ${sum} EUR, expected ${total} EUR    values=False
```

- `VAR    &{NOTES}    &{NOTES}    ${value}=${count}    scope=TEST` creates a new dictionary from the current one plus the new entry, so the declared default stays empty. Two tests in a row show it: the first loads 10 notes of 20 EUR and 4 of 50 EUR (400 EUR); the second loads 2 notes of 100 EUR and expects 200 EUR. With `Set To Dictionary` the second test sees 600 EUR; with `VAR` it sees 200 EUR.
- For a list, write `VAR    @{ITEMS}    @{ITEMS}    ${new}    scope=TEST`.

## World-library strategy

A Python library with `@library(scope="TEST")` keeps the state on the instance and implements the steps as `@keyword("…")` sentences. Robot Framework creates a new instance for every test, so nothing is declared and nothing leaks. The runnable project is `assets/examples/world-strategy/`, with the library in `lib/CashWithdrawalWorld.py`.

- The `@keyword` name is the sentence; the method name isn't visible to readers.
- Type hints (`amount: int`) convert embedded arguments, like `${amount: int}` in a resource.
- Docstrings become the step documentation that `robotcode doc keywords` shows.
- Fail with `AssertionError` and a domain message; don't return `False`.
- Choose it when steps need real logic (parsing, calculation, retries), when the team prefers Python, or when the project already has one. The test files read the same under both strategies.
- Writing and checking the library itself: see the `rf-python-library` skill.

## What not to do

| Pattern | Problem |
|---|---|
| `VAR … scope=TEST` without a declaration | `VariableNotFound` from robotcode on every step that reads it |
| `Set Test Variable`, `Set Suite Variable`, `Set Global Variable` | the same analysis errors; suite and global scope leak between tests |
| `Set To Dictionary` or `Append To List` on a declared container | leaks into the next test |
| business state in `Suite Setup` | tests depend on run order |
| a `Then` that reads what a previous test created | tests are no longer independent |
| a value returned from a step into the test body (`${x}    When …`) | test bodies hold only sentences; keep the value in scenario state |
