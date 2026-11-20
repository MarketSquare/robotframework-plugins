# Reviewing BDD Suites

- [Gather evidence](#gather-evidence)
- [S1: correctness and analysis](#s1-correctness-and-analysis)
- [S2: layering and independence](#s2-layering-and-independence)
- [S3: language and style](#s3-language-and-style)
- [Findings format](#findings-format)

A review answers two questions: can a business reader understand and trust these specifications, and will they stay consistent as the suite grows? Gather tool evidence first, then read every test and step against the checks below. In review mode, don't edit files unless the user asks for fixes.

## Gather evidence

| Command | Shows |
|---|---|
| `robotcode analyze code <paths>` | `KeywordNotFound` (typos, undefined steps), `MultipleKeywords` (ambiguous steps), `VariableNotFound` (undeclared state), `PrivateKeyword` (tests calling helpers), `VariableNotReplaced` (`${var}` in templated test names) |
| `robotcode doc keywords <steps resource or library>` | the vocabulary: synonyms, overlapping sentences, missing documentation |
| `robotcode discover tags` | tags outside the `feature:` and `rule:` scheme, two spellings of one tag |
| `robotcode discover tests --search "<term>"` | where a behaviour is already specified |
| `robocop check --no-cache <paths>` with the project's configuration | naming (NAME02, NAME18), missing documentation (DOC01 to DOC03), shared tags (TAG05), test-scope variables outside steps resources (VAR06) |
| `robotcode robot --dryrun` on the suite | steps that don't resolve, and a `Test Setup` from `__init__.robot` that a child suite can't find |

## S1: correctness and analysis

| ID | Problem | Detect | Fix |
|---|---|---|---|
| C1 | undefined, mistyped or ambiguous step | analyze: `KeywordNotFound`, `MultipleKeywords`; dry run | reuse the existing sentence; restrict values with types or patterns |
| C2 | trailing catch-all argument (`The order "${id}" is ${state}`) that swallows typos | read the step definitions | `${state:paid\|shipped\|cancelled}` |
| C3 | scenario state not declared | analyze: `VariableNotFound` on state | declare it in `*** Variables ***` of the steps resource |
| C4 | a declared list or dictionary changed in place, so state leaks into the next test | `Set To Dictionary`, `Append To List`, `Remove From …` on declared variables | `VAR    &{NOTES}    &{NOTES}    ${k}=${v}    scope=TEST` |
| C5 | a `Then` step that can't fail (only logs, or returns a boolean) | read the body; break the expected value and run | assert with `Should …` or raise `AssertionError` |
| C6 | a template for external data rows with embedded arguments | `Variable '${…}' not found` at run time; the dry run passes | a template keyword with normal `[Arguments]` |
| C7 | child suite of a feature directory without the steps import | `Setup failed: No keyword with name 'Given …'` | import the steps resource in every child suite |

## S2: layering and independence

| ID | Problem | Detect | Fix |
|---|---|---|---|
| L1 | library keywords, locators, URLs, HTTP verbs or SQL in a test body | any line that isn't a prefixed step or a template row; analyze `PrivateKeyword` | move the mechanics into a step; the test keeps the sentence |
| L2 | a UI script as steps: clicks, typing, navigation | steps name fields, buttons, pages, "click", "type", "open" | one declarative step per intent: `When Alice withdraws 20 EUR` |
| L3 | a test that depends on another test's state or order | no `Given` of its own; a `Then` reading what an earlier test created | give each test its own `Given` |
| L4 | business state in `Suite Setup`, hooks or listeners | read `Suite Setup` and `__init__.robot` | a visible `Given`, or `Test Setup    Given …` |
| L5 | a Background (`Test Setup`) that only one test needs | count the tests that rely on it | inline it as that test's first `Given`, or split the file |
| L6 | repeated phases (`When … Then … When … Then …`) | read the prefix order | one test per behaviour |
| L7 | several behaviours in one test, or 10 or more steps | "and" in the test name; unrelated `Then`s | split; name the starting state in one sentence |
| L8 | a BDD prefix in a keyword name, or steps calling steps with prefixes | read keyword names and bodies | drop the prefix from the name; share logic through a technical keyword |
| L9 | values returned from steps into the test body (`${result}    When …`) | read test bodies | keep the value in scenario state |

## S3: language and style

| ID | Problem | Detect | Fix |
|---|---|---|---|
| W1 | conjunction step with two facts or actions | "and", "then" or commas inside a step | split into `And` steps |
| W2 | vague outcome: `Then it works`, `the result is correct` | read the `Then` steps | name what the user or system shows |
| W3 | placeholder data: `foo`, `test`, `user1`, `123` | read arguments and rows | realistic values: `Alice`, `100 EUR` |
| W4 | synonym steps for one concept | `robotcode doc keywords` | keep one sentence, replace the others |
| W5 | unnamed template rows that need explaining, or `${variables}` in example names | analyze `VariableNotReplaced`; names like `Example 1` | one named test per example |
| W6 | missing feature documentation: no story, no `Metadata    Feature`, no `feature:` tag | Robocop DOC03; read `*** Settings ***` | add the story, the metadata and the tag |
| W7 | missing rule documentation or `rule:` tag | Robocop DOC02; read the tests | add the `Rule:` sentence and the tag |
| W8 | missing step documentation | Robocop DOC01; `robotcode doc keywords` | one line on what the step establishes, does or checks |
| W9 | tags outside the vocabulary, two spellings, descriptions as tags | `robotcode discover tags` | `feature:` and `rule:` plus the project's tags |
| W10 | step casing that breaks the project's convention | read the steps; Robocop NAME02 and NAME18 with the project's configuration | the project's casing; sentence style when the project has none |
| W11 | first person, past tense or imperative steps (`I withdrew`, `Withdraw 20 EUR`) | read the steps | third person, present tense |
| W12 | test names that describe the procedure (`Test withdraw 2`) | read the names | name the behaviour |
| W13 | strings without quotes, or quotes around numbers | read the steps | `"Insufficient funds"`, but `20 EUR` |
| W14 | oversized outlines (20 or more rows) | count the rows | keep representative examples |
| W15 | imports that break the project's convention | read the imports in `*** Settings ***` | the project's style; by name with `python-path` when it has none |
| W16 | an outline sentence that doesn't fit every row (`1 days late`), or an `IF` in a template keyword | read the rows as sentences | a named test for the odd row |

## Findings format

Order findings by severity (S1, then S2, then S3), and within a severity by the number of tests affected. Write each finding on one line that starts with the check ID, then the location, then the problem, why it matters and the rewrite:

```text
ID — file:line — problem. Why: one sentence. Rewrite: the replacement.
```

Given this test:

```robotframework
# Wrong: a procedural test with technical keywords in its body.
*** Test Cases ***
Test withdraw 2
    Open Account    user1    100
    Given user1 is logged in and has money
    When user1 withdraws 20
    Then it works
```

the review reports:

```text
L1 — tests/withdrawal.robot:12 — library keyword Open Account in a test body. Why: a business reader can't tell what is specified. Rewrite: Given Alice has a balance of 100 EUR
W1 — tests/withdrawal.robot:13 — conjunction step "is logged in and has money". Why: neither fact can be reused. Rewrite: Given Alice is signed in / And Alice has a balance of 100 EUR
W2 — tests/withdrawal.robot:15 — vague outcome "it works". Why: the test passes as long as nothing crashes. Rewrite: Then the ATM dispenses 20 EUR / And Alice's balance is 80 EUR
W3 — tests/withdrawal.robot:13 — placeholder data user1. Why: it says nothing about the example. Rewrite: Alice, with amounts in EUR
W12 — tests/withdrawal.robot:11 — procedural test name "Test withdraw 2". Why: the report doesn't say what behaviour failed. Rewrite: Account holder withdraws cash within their balance
```

End with a short summary: the count per severity, the three changes with the biggest effect, and the tool results (analysis errors, Robocop findings) before and, if fixes were applied, after.
