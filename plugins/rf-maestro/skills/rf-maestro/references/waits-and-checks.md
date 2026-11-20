# Waits, Expect and Should keywords

Read this when a test fails because an element was not there yet, or when choosing between a wait, an `Expect` and a `Should` check.

## Which one to use

| Need | Keyword | Retries |
|---|---|---|
| An element appears or goes, then the test goes on | `Wait Until Page Contains Element    <locator>`, `Wait Until Element Is Visible`, `Wait Until Page Does Not Contain Element` | yes, for `timeout` |
| Text appears or goes | `Wait Until Page Contains    <text>`, `Wait Until Page Does Not Contain` | yes, for `timeout` |
| A state, with a clear failure message | `Expect Element    <locator>    visible` (or `not visible`, `enabled`, `disabled`), `Expect Text    <text>    visible` | yes, for `timeout` |
| Check the screen as it is now | `Page Should Contain Element`, `Page Should Contain Text`, `Element Should Contain Text`, `Element Text Should Be` | no |
| Read a value now | `Get Text`, `Get Element Attribute` | no |
| Wait for an animation to finish | `Wait For Animation To End` | yes, bounded |

Every action (`Click Text`, `Tap`, `Input Text`, `Swipe`) waits for its own element. Add a wait only before a check or before a first action on a screen that is still loading.

## Timeouts

- The import argument `timeout` sets the default for the `Wait Until` and `Expect` keywords. The default is 5 seconds; `timeout=10s` suits most emulators.
- `Expect Element` and `Expect Text` take their own `timeout=` argument, which overrides the import value for that call.
- `Set Maestro Timeout    <seconds>` changes the timeout for the Maestro commands, and `Get Maestro Timeout` reads it back.
- `retry_interval` and `loglevel` are accepted for AppiumLibrary compatibility. Maestro polls on its own, so the interval is ignored.

## Expect states

| State | Passes when |
|---|---|
| `visible` | the element is on screen |
| `not visible` | the element is not on screen |
| `enabled` | the element is on screen and enabled |
| `disabled` | the element is on screen and disabled |

`Expect Text` adds the `exact_match` argument. Without it the text is matched as part of a longer label.

## Should keywords and failures

A `Should` keyword that fails logs the screen source at the log level it was given, then raises. Read the source in the log before you change the locator. `Page Should Not Contain Element` and `Element Should Not Contain Text` are the negated forms.

## The speed argument

`speed=0.5s` on the import pauses before every Maestro command, the way SeleniumLibrary's `speed` does. Raise it when a slow emulator stops answering between commands. Lower values are not a fix for a slow run; a rushed run reads half-drawn screens.

## Do not sleep

Use the waits above instead of `Sleep` between steps. A poll that waits for backend data belongs in `Wait Until Keyword Succeeds` around a read that does not touch the app.
