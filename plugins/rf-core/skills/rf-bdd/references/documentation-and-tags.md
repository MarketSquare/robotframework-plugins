# Documentation, Metadata and Tags

- [Where each piece goes](#where-each-piece-goes)
- [Suite documentation and Metadata](#suite-documentation-and-metadata)
- [Feature directories and capability areas](#feature-directories-and-capability-areas)
- [Test documentation](#test-documentation)
- [The tag scheme](#the-tag-scheme)
- [Tag documentation and links](#tag-documentation-and-links)
- [Localised specifications](#localised-specifications)

The report and the log are the living documentation of a BDD suite. They show the user story, every rule with its examples, every step in domain words, and a pass/fail count per feature and per rule, when the suite fills in the right fields. Code blocks run in a copy of `assets/examples/resource-strategy/`.

## Where each piece goes

| Content | Field | Shows up in |
|---|---|---|
| user story and feature description | suite `Documentation` | top of the report and the log for that suite |
| feature name | `Metadata    Feature    <name>` | suite metadata in the report and the log |
| capability area description | `Documentation` in the directory's `__init__.robot` | the parent suite |
| rule | test `[Documentation]    Rule: …` and a `rule:<slug>` tag | test details; one row per rule in the tag statistics |
| ticket or requirement | `issue:<id>` tag, or test `[Metadata]` on RF 7.5+ | test details |
| meaning of a step | step `[Documentation]` or docstring; the steps resource is the glossary | `robotcode doc keywords`, editor hover |
| meaning of a tag | `tag-doc` in `robot.toml` | tooltip in the tag statistics |

## Suite documentation and Metadata

`assets/examples/resource-strategy/tests/cash_withdrawal/__init__.robot` shows the settings of a feature:
- The first three `Documentation` lines are the user story ("As a … / I want … / So that …"), without a "Feature:" prefix. After an empty `...` line, a few sentences of business context may follow.
- `Metadata    Feature    <Name>` uses the feature name. Keep the key `Feature` in every language, because filters and tools rely on it.
- More metadata is fine when it helps a reader: `Metadata    Specification    https://wiki.example.com/atm`.
- Robot Framework names the suite after the file, so name files after the feature: `cash_withdrawal.robot` becomes "Cash Withdrawal".

## Feature directories and capability areas

Group features into directories by business capability, not by technical layer:

```text
tests/
  __init__.robot              Documentation: "Self-service banking at the ATM."
  cash_withdrawal/            a feature directory (it has an outline)
    __init__.robot            story, Metadata, Test Tags, Test Setup
    withdrawal_rules.robot
    remaining_balance.robot
  daily_withdrawal_limit.robot
```

- A capability area's `__init__.robot` holds a short `Documentation`, and at most technical `Suite Setup` and `Suite Teardown`, never business state.
- A feature directory's `__init__.robot` holds the story, `Metadata    Feature`, `Test Tags    feature:<slug>` and the Background as `Test Setup`.
- Each child suite imports the steps resource itself, also for the `Test Setup` it inherits. Without the import, every test in that child fails with `Setup failed: No keyword with name 'Given …' found`. The dry run shows this; `robotcode analyze code` doesn't.
- What `__init__.robot` may contain and which imports child suites see: see the `rf-language` skill.

## Test documentation

- `[Documentation]` starts with `Rule:` and states the rule in one sentence. Tests that illustrate the same rule repeat the sentence word for word.
- Don't repeat the steps in the documentation; the body already says it.
- Link tickets with an `issue:<id>` tag. Test-level `[Metadata]    Issue    BANK-123` needs Robot Framework 7.5; on 7.4 and older it fails the test with "Setting 'Metadata' is not allowed with tests or tasks". Use it only after the version gate allows it.
- Settings come first in the body: `[Documentation]`, `[Tags]`, then `[Setup]` or `[Template]`.

## The tag scheme

| Tag | Where | Meaning |
|---|---|---|
| `feature:<slug>` | `Test Tags` of the feature's file or its `__init__.robot` | the feature the test specifies |
| `rule:<slug>` | `[Tags]` per test; `Test Tags` when every test in the file has the same rule | the rule the test illustrates |
| the project's own tags (`smoke`, `wip`) | `[Tags]` | what the project already uses them for |

- Slugs are lower-case kebab case, from the feature name and the rule wording: `feature:cash-withdrawal`, `rule:no-overdraft`.
- Check the existing tags first with `robotcode discover tags`. Reuse a tag with the same meaning; don't add a second spelling.
- Descriptions go in `[Documentation]`, not in tags.
- Reserved `robot:` tags, tag patterns and selecting tests on the command line: see the `rf-language` skill.

## Tag documentation and links

Explain the tag scheme once in `robot.toml`, so the tag statistics get tooltips and links:

```toml
[tag-doc]
"feature?*" = "Feature the test specifies"
"rule?*" = "Business rule the test illustrates"

[tag-stat-link]
"rule?*" = "https://wiki.example.com/rules/%2:Rule description"
```

- Write `?` instead of the colon in these patterns (`rule?*`, not `rule:*`). Robot Framework splits the option at the first colon, so `rule:*` becomes the pattern `rule`, which matches no `rule:<slug>` tag. You get no tooltip, no link and no error.
- `%N` is what the N-th wildcard matched. In `rule?*`, `%1` is the colon and `%2` is the slug, so `rule:no-overdraft` links to `…/rules/no-overdraft`.
- Check the effective settings with `robotcode profiles show`.

## Localised specifications

When the business speaks another language, write the whole specification in it: headers, settings, prefixes and step sentences. Start each file with `Language: <language>`, or set `languages = ["de"]` in `robot.toml`. Technical keywords below the steps can stay in English.

The block below keeps the steps in the suite so that it runs on its own; in a project they go into `bargeld_steps.resource`.

<!-- file: tests/bargeldabhebung.robot -->
```robotframework
Language: German

*** Einstellungen ***
Dokumentation       Als Kontoinhaberin
...                 möchte ich am Geldautomaten Bargeld abheben,
...                 damit ich auch außerhalb der Öffnungszeiten an Geld komme.
Metadaten           Feature    Bargeldabhebung
Bibliothek          AtmService
Testmarker          feature:bargeldabhebung


*** Testfälle ***
Abhebung innerhalb des Guthabens wird abgebucht
    [Dokumentation]    Regel: Eine Abhebung innerhalb des Guthabens wird ausgezahlt und abgebucht.
    [Marker]    rule:abbuchung-bei-auszahlung
    Angenommen Alice hat ein Guthaben von 100 EUR
    Wenn Alice 20 EUR abhebt
    Dann beträgt das Guthaben von Alice 80 EUR


*** Schlüsselwörter ***
${inhaber} hat ein Guthaben von ${betrag: int} EUR
    [Dokumentation]    Eröffnet ein Konto für ``inhaber`` mit ``betrag`` Euro.
    Open Account    ${inhaber}    ${betrag}

${inhaber} ${betrag: int} EUR abhebt
    [Dokumentation]    ``inhaber`` fordert ``betrag`` Euro am Geldautomaten an.
    Request Withdrawal    ${inhaber}    ${betrag}

Beträgt das Guthaben von ${inhaber} ${betrag: int} EUR
    [Dokumentation]    Das Konto von ``inhaber`` enthält genau ``betrag`` Euro.
    ${guthaben}    Get Balance    ${inhaber}
    Should Be Equal    ${guthaben}    ${betrag}
```

| English | German |
|---|---|
| `*** Settings ***`, `*** Variables ***`, `*** Test Cases ***`, `*** Keywords ***` | `*** Einstellungen ***`, `*** Variablen ***`, `*** Testfälle ***`, `*** Schlüsselwörter ***` |
| `Documentation`, `Metadata`, `Library`, `Resource` | `Dokumentation`, `Metadaten`, `Bibliothek`, `Ressource` |
| `Test Setup`, `Test Tags`, `Test Template` | `Testvorbereitung`, `Testmarker`, `Testvorlage` |
| `[Tags]`, `[Template]`, `[Arguments]` | `[Marker]`, `[Vorlage]`, `[Argumente]` |
| `Given`, `When`, `Then`, `And`, `But` | `Angenommen`, `Wenn`, `Dann`, `Und`, `Aber` |

- Write natural grammar for the prefix. In German the prefix decides the word order: after `Wenn` the verb goes last (`Wenn Alice 20 EUR abhebt`), after `Dann` it comes second (`Dann beträgt das Guthaben von Alice 80 EUR`). So a German sentence usually belongs to one phase; define a second sentence when another phase needs it.
- Avoid possessives glued to an argument (`${inhaber}s Guthaben`); write `Das Guthaben von ${inhaber}`.
- Rule documentation uses the local word (`Regel:`). Keep the `feature:` and `rule:` tag prefixes in every language.
- Messages from the system under test stay as the system produces them.
- List the translations for another language from the project's environment:

```bash
python -c "from robot.conf.languages import Language; l = Language.from_name('fi'); print({k: getattr(l, k) for k in dir(l) if k.endswith(('_header', '_setting', '_prefixes'))})"
```
