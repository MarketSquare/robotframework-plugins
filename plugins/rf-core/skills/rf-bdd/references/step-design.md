# Designing Step Keywords

- [Sentence rules](#sentence-rules)
- [Naming](#naming)
- [Declarative, not procedural](#declarative-not-procedural)
- [Embedded arguments in steps](#embedded-arguments-in-steps)
- [Catch-all and ambiguous steps](#catch-all-and-ambiguous-steps)
- [Reusing the vocabulary](#reusing-the-vocabulary)
- [What goes inside a step](#what-goes-inside-a-step)

A step keyword is one sentence of the domain language, and test cases are made of these sentences. This reference covers how to word, name and parameterise them, keep them unambiguous and reuse them. Code blocks run in a copy of `assets/examples/resource-strategy/`.

## Sentence rules

| Rule | Good | Bad |
|---|---|---|
| third person, present tense | `Alice withdraws 20 EUR` | `I withdrew 20 EUR`, `Withdraw 20 EUR` |
| subject and predicate | `The ATM dispenses 20 EUR` | `Dispensing of 20 EUR` |
| one idea per step | `Given Alice has a balance of 100 EUR` and `And Alice has already withdrawn 50 EUR today` | `Given Alice has 100 EUR and has withdrawn 50 EUR` |
| an observable outcome in `Then` | `Then the withdrawal is refused with "Insufficient funds"` | `Then it fails`, `Then the result is correct` |
| concrete, realistic data | `Alice`, `100 EUR`, `2026-08-31` | `user1`, `foo`, `123` |
| strings in double quotes | `is refused with "Insufficient funds"` | `is refused with Insufficient funds` |
| one word per concept | always "account holder", always "withdraws" | "customer" here, "user" there |
| grammatical for every value | `Alice has borrowed 3 books`, plus `Alice has borrowed one book` | `Alice has borrowed 1 books`, `${n} book(s)` |

Write the sentence first and read it aloud inside its scenario. If it only makes sense to someone who knows the implementation, reword it.

## Naming

- Step 0 decides the casing. Follow the casing of the project's existing step keywords. A Title Case project (`The Cart Contains ${count} Items`) gets Title Case steps, and its Robocop configuration stays as it is.
- With no existing steps, the default is sentence style: only the first word capitalized, apart from names, acronyms and units (`The ATM dispenses ${amount: int} EUR`). A definition may start with an embedded argument (`${holder} has a balance of ${amount: int} EUR`); a BDD prefix before it needs Robot Framework 7.1. Merge `assets/robocop-bdd.toml` into the project's Robocop configuration so Robocop accepts this style.
- Calls put the prefix first and continue in the step's casing: `Then the ATM dispenses 20 EUR`. Name matching is case-insensitive.
- Never put `Given`, `When`, `Then`, `And` or `But` in a keyword name. A keyword defined as `Given the app is open` can't be called as `When the app is open`.
- Technical keywords below the steps keep Title Case (`Request Withdrawal`), so the layer shows in the name.
- Name step resources `<domain>_steps.resource`. The Robocop asset relies on this name.
- Every step keyword has `[Documentation]` (or a docstring in a Python library) that says what it establishes, does or checks. `robotcode doc keywords` shows the first line, so the steps resource becomes the domain glossary.

## Declarative, not procedural

Steps say what happens in the domain, not how a user operates the screen. The sentence should make sense without a computer.

```robotframework
# Wrong: a UI script written as steps.
*** Test Cases ***
Alice withdraws cash
    Given Alice opens the login page
    When Alice types "alice@example.com" into the e-mail field
    And Alice clicks "Withdraw"
    And Alice types "20" into "#amount"
    Then the element "div.result" contains "Please take your cash"
```

The declarative form is the test `Account holder withdraws cash within their balance` in `assets/examples/resource-strategy/tests/cash_withdrawal/withdrawal_rules.robot`: `Given Alice has a balance of 100 EUR`, `When Alice withdraws 20 EUR`, `Then the ATM dispenses 20 EUR`.

- The clicks and fields still exist, inside the `Alice withdraws 20 EUR` step or the technical keywords it calls.
- Navigation belongs in a test only when navigation is the behaviour under test.
- A `Given` sets the starting state as directly as the system allows (an API call, a fixture) and states it as a fact: `Given Alice is signed in as an "Editor"`.

## Embedded arguments in steps

| Form | Use it for | Example |
|---|---|---|
| `"${name}"` | any string, including several words | `is refused with "${reason}"` |
| `${name: int}` | numbers, dates and other typed values (RF 7.3+) | `${amount: int} EUR` |
| `${name:regex}` | restricting what may match | `card "${number:\d{4} \d{4}}"` |
| `${name:a\|b}` | a closed set of words | `is ${outcome:dispensed\|refused}` |
| embedded plus `[Arguments]` | tables, lists and text after a sentence | `The receipt reads` with `@{lines}` |

- Before Robot Framework 7.3, write `${amount:\d+}` and convert in the body: `${amount}    Convert To Integer    ${amount}`.
- Quote every string value, or restrict it with a pattern. Steps often put two values next to each other, and an unrestricted value takes the shortest match.
- An embedded argument can't be optional, and literal text in the name is matched exactly: `day(s)` matches only the characters `day(s)`. Write two sentences instead.
- Matching rules, custom patterns and conflicts between keywords: see the `rf-language` skill.

## Catch-all and ambiguous steps

When several step keywords match a call, Robot Framework picks the more specific one without telling you, and a dry run passes either way. The risk is a step that quietly matches the wrong sentence:

```robotframework
# Wrong: a trailing catch-all. "is payed" and "is anything" both match.
*** Keywords ***
The order "${id}" is ${state}
    [Documentation]    Catch-all state check.
    Log    ${id} ${state}
```

A typo such as `Then the order "42" is payed` binds to it and fails with a confusing message, or passes. Restrict the trailing value instead, so robotcode reports `KeywordNotFound` for the typo before anything runs:

A test then reads `Then the withdrawal is dispensed` or `Then the withdrawal is refused with "Insufficient funds"`, and both sentences resolve to one keyword each:

<!-- file: resources/withdrawal_outcome_steps.resource -->
```robotframework
*** Settings ***
Documentation       Step definitions for withdrawal outcomes.
Resource            cash_withdrawal_steps.resource


*** Keywords ***
The withdrawal is ${outcome:dispensed|refused}
    [Documentation]    The last withdrawal ended with ``outcome``.
    Withdrawal Outcome Should Be    ${outcome}

Withdrawal Outcome Should Be
    [Documentation]    Technical check shared by the outcome steps.
    [Tags]    robot:private
    [Arguments]    ${expected}
    Should Be Equal    ${LAST_WITHDRAWAL}[status]    ${expected}
    ...    msg=Expected the withdrawal to be ${expected}, but it was ${LAST_WITHDRAWAL}[status]    values=False
```

- No trailing catch-alls. A value at the end of a sentence matches anything; give it a type, an alternation or a pattern.
- Check a new sentence against the existing ones. `The withdrawal is ${outcome:dispensed|refused}` can't match `the withdrawal is refused with "…"`, because the whole name has to match.
- A stricter pattern alone doesn't make one keyword win over another; robotcode reports `MultipleKeywords`. Rename one of them.
- Only a real run shows which keyword and which values a step bound to.

## Reusing the vocabulary

Before writing a step:
1. List the existing sentences: `robotcode doc keywords resources/cash_withdrawal_steps.resource`, or add a filter such as `"balance"`.
2. If one has the right meaning, use it as written, even if you would word it differently.
3. If one is close but needs another value, generalise it with a typed argument instead of adding a near-copy.
4. Only then add a sentence to the project's existing steps resource or library for that domain. Create a new `<domain>_steps.resource` only for a new domain.

Signs of drift: `The user is logged in` next to `The user has signed in`; `${holder} has ${amount} EUR` next to `${holder} has a balance of ${amount} EUR`; one concept called "customer", "client" and "account holder".

## What goes inside a step

- Steps call technical keywords: library keywords, the project's API client, or Title Case helpers. Tag helpers in a steps resource `[Tags]    robot:private`; robotcode then warns (`PrivateKeyword`) when a test calls them.
- Steps don't call other steps with prefixes. Share logic through a technical keyword.
- A `Then` step asserts with a message in domain words, such as `msg=Expected the withdrawal to be dispensed, but it was refused`.
- A `Given` that can fail checks its own precondition (`Precondition failed: the earlier withdrawal of 200 EUR was refused`), so a broken setup doesn't surface later as a confusing assertion.
- Several lines of mechanics belong in a technical keyword.

| Phase | Does | Avoid |
|---|---|---|
| `Given` | sets the starting state, as a fact | UI navigation; assertions on the system |
| `When` | one domain action; keeps its result as scenario state | several actions; assertions |
| `Then` | reads an observable outcome and asserts with a domain message | internal columns, private fields, log lines |
