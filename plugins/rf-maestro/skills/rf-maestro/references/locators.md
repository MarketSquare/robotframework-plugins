# Locators in MaestroLibrary

Read this when choosing a locator, when a locator matches nothing, or when a Flutter or Compose screen exposes no ids.

## Strategies

| Strategy | Example | Matches |
|---|---|---|
| `id` | `id=login_button` | the whole resource-id on Android, or the Flutter `Semantics(identifier: ...)` value |
| `text` | `text=Log in` | the whole text, content-desc or hint, literally |
| `accessibility_id` | `accessibility_id=Back` | the same as `text` (Maestro matches content-desc as text) |
| `regex` | `regex=Log.*` | text, as a Maestro (Java) regular expression |
| `id_regex` | `id_regex=.*login` | the id, as a regular expression |
| `point` | `point=50%,90%` | a screen position, in percent or pixels |

A locator with no strategy is text. Flutter widgets expose text far more often than ids, so the bare form is the usual choice there.

## Order of preference

1. `id=` with a test id the app sets. It is stable across languages.
2. `text=` or a bare text when the screen shows a stable label.
3. `regex=` or `id_regex=` when the text varies, for example a count or a date.
4. `point=` only while exploring a new screen. A position breaks when the layout changes.

## Strategies that fail at once

`xpath=`, `class=`, `android=`, `ios=`, `predicate=`, `chain=`, `css=`, `name=` and `identifier=` have no Maestro equivalent. The library stops with a message that names the strategy. Rewrite the locator with `id=`, `text=` or `regex=`.

## Regular expressions

Actions match on the device with Java regular expressions. `Should` and `Get` keywords match the screen with Python's `re`. The two agree for literal text and common patterns. Keep `regex=` and `id_regex=` to syntax both engines share: no possessive quantifiers, no `\p{...}` classes and no inline flags.

## Read the screen

When no locator fits, read the screen source once and pick from it:

```robotframework
${source}=    Get Source
Log Source    loglevel=INFO
${label}=     Get Text    id=screen_title
```

`Get Element Attribute    <locator>    <attribute>` reads one attribute of the first match. `Get Text` returns the text of the first match; use `first_only=False` for a list of all matches.

## Multiple matches

`text=` matches the whole text, literally. A label with a variable part (a count, a name) needs `regex=`. `Click Text` and `Expect Text` are the exception: they match text that contains the given string unless `exact_match=True` is set. When a screen repeats a label, prefer an `id=` locator.

## Scrolled-off elements

`Scroll Element Into View` and `Scroll Down` move the screen until the locator shows. Give the locator of the element itself, not of its container. The gesture keywords are listed in SKILL.md.
