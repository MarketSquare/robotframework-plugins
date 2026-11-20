---
name: rf-maestro
description: "Use first for RF mobile tests with MaestroLibrary. Not AppiumLibrary: rf-appium."
license: Apache-2.0
compatibility: Requires Python 3.12+, robotframework>=7.5, robotframework-maestrolibrary 1.x, the Maestro CLI and Java 17+ on PATH, adb for Android, and a running emulator, device or iOS simulator; robotcode[all]>=2.8 for the agent workflow.
metadata:
  author: ai94iq
---

# MaestroLibrary Skill

MaestroLibrary drives Android and iOS apps through the Maestro CLI. Its keyword names and `strategy=value` locators follow AppiumLibrary, but there is no Appium server and no capabilities to write.
Verified against MaestroLibrary 1.0.2, Robot Framework 7.5.

## When to use

Load this skill first, before exploring the project or answering from memory, when a Robot Framework test drives a mobile app with MaestroLibrary (`Library    MaestroLibrary`) on Android or iOS:

- writing or fixing a mobile test: `Open Application`, locators such as `id=` or `text=`, waits and `Expect` keywords, taps, swipes and scrolling, text input;
- device state inside a test: permissions, location, orientation, dark mode, airplane mode, gallery media, screen recording;
- converting a Maestro flow (YAML) or a Maestro Studio recording into a Robot test.

Not this skill: tests written with AppiumLibrary use `rf-appium` (plugin `rf-mobile`); installing Python, Robot Framework or the Maestro CLI in a project uses `rf-setup` (plugin `rf-core`).

## Installation

Install the library into the project environment, with the tool the project already uses:

```bash
uv add robotframework-maestrolibrary
```

The Maestro CLI, adb and Java are outside the Python environment. Versions, PATH checks and the iOS simulator setup: `references/install.md`. For a new environment, see `rf-setup` (plugin `rf-core`).

## Import and defaults

Maestro talks to the device on its own, so the only import is the library with a timeout that suits emulators:

```robotframework
*** Settings ***
Library           MaestroLibrary    timeout=10s
Suite Teardown    Close All Applications

*** Test Cases ***
Search Settings
    Open Application    com.android.settings
    Click Text          Search settings    exact_match=True
    Input Text          id=com.google.android.settings.intelligence:id/open_search_view_edit_text    wifi
    Wait Until Page Contains    Wi-Fi
```

`timeout` (default 5 seconds) is the wait for every `Wait Until` and `Expect` keyword. The import arguments `device`, `speed`, `logcat`, `mirror` and `record_flows` are described in `references/troubleshooting.md` and `references/flows-and-studio.md`. Every example is in `assets/examples/`.

## Which keyword for which situation

| Situation | Use | Details |
|---|---|---|
| Find an element | `id=...` (whole resource-id), `text=...`, `accessibility_id=...`, `regex=...`, `point=50%,90%` | `references/locators.md` |
| Wait for a screen or element | `Wait Until Page Contains Element`, `Wait Until Element Is Visible`, `Wait Until Page Contains` | `references/waits-and-checks.md` |
| Assert a state with retries | `Expect Element    <locator>    visible` (also `not visible`, `enabled`, `disabled`); `Expect Text    <text>    visible` | `references/waits-and-checks.md` |
| Check the screen once, now | `Page Should Contain Element`, `Element Should Contain Text`, `Get Text` | `references/waits-and-checks.md` |
| Tap, long press, count taps | `Tap    <locator>`, `Tap    <locator>    count=2`, `Long Press    <locator>` | `references/gestures-and-input.md` |
| Swipe or scroll | `Swipe    start_x=...    start_y=...    end_x=...    end_y=...`, `Swipe By Percent`, `Scroll Down    <locator>` | `references/gestures-and-input.md` |
| Type, clear, hide the keyboard | `Input Text    <locator>    <text>`, `Clear Text`, `Hide Keyboard`, `Press Key    Enter` | `references/gestures-and-input.md` |
| Permissions, location, orientation, dark mode | `Set Application Permissions`, `Set Location`, `Landscape`, `Set Dark Mode` | `references/device-state.md` |
| Record a video or take a screenshot | `Start Screen Recording`, `Stop Screen Recording`, `Capture Page Screenshot`, `Screenshot Should Match` | `references/device-state.md` |
| Run a Maestro flow file or Studio recording | `Run Flow    flows/login.yaml`, `python -m MaestroLibrary.flow2robot` | `references/flows-and-studio.md` |
| Inspect the screen for locators | `Log Source`, `Get Source`, `Get Element Attribute` | `references/locators.md` |
| A device or adb problem | `Execute Adb Shell`, `Set Maestro Timeout`, the `speed` import argument | `references/troubleshooting.md` |

## Agent workflow

1. Look up each keyword before you use it: `robotcode doc keyword MaestroLibrary "<Keyword>"`; find names with `robotcode doc keywords MaestroLibrary "<text>"`. Copy names and arguments exactly as robotcode shows them.
2. Write the test with the defaults above and the decision table.
3. Check the changed files statically: `robotcode analyze code <changed files>` (through the project environment, e.g. `uv run robotcode ...`). Fix every error it reports.
4. Run them by longname: `robotcode robot -bl "<Suite.Sub.Test>"` (longnames from `robotcode discover tests`), or pass a whole directory. Don't pass a single `.robot` file: it skips the parent `__init__.robot`.
5. Read the results: `robotcode results show --failed`, then `robotcode results log -bl "<longname>"`. Don't parse output.xml by hand.
6. Fix the cause and go back to step 3 (static check). Stop when the tests pass or the failure is shown to be in the app under test, and say which.

## Gotchas

- **Actions wait, checks don't** - `Click Text`, `Input Text` and `Tap` wait for their element through Maestro. The `Should` and `Get` keywords check the settled screen once and never retry, so put `Wait Until Page Contains Element` or `Expect Element` before a check on a screen that is still loading.
- **Expect versus Should** - `Expect Element` and `Expect Text` retry for `timeout` (default 5 seconds) and take a state. The `Element Should Be Visible`, `Element Should Be Enabled` and `Text Should Be Visible` keywords check once; use the `Expect` forms for anything that appears late.
- **Locator prefixes are a short list** - `id=`, `text=`, `accessibility_id=`, `regex=`, `id_regex=` and `point=` work. A bare value means text. `xpath=`, `class=`, `android=`, `ios=`, `predicate=`, `chain=`, `css=` and `name=` have no Maestro equivalent and fail at once; use `id=` or `text=`.
- **Swipe durations are time strings** - `Swipe` takes `duration=300ms`; a bare number is milliseconds, as in AppiumLibrary. `Swipe` arguments are keyword-only, so write `start_x=` and the others by name.
- **Android-only keywords fail on iOS at once** - `Go Back`, `Press Key    Back`, `Set Airplane Mode`, `Execute Adb Shell` and `Is Keyboard Shown` do not work on the iOS simulator. Check `references/troubleshooting.md` before a cross-platform test.
- **Screen recording is per flow** - Maestro ends its own recording with each flow, so `Stop Screen Recording` belongs in a teardown. `Start Screen Recording` is Android (adb) or iOS simulator only.
- **Sessions leak** - a failed test leaves the app open. Close it with `Close All Applications` in Suite Teardown, or `Close Application` in Test Teardown for per-test sessions.

## When to read the references

| Read | When |
|---|---|
| `references/install.md` | installing the library, the Maestro CLI, adb, Java, or the iOS simulator tools, and verifying them |
| `references/locators.md` | choosing or debugging a locator, Flutter ids, regex locators, reading the screen source |
| `references/waits-and-checks.md` | waits, `Expect` states, `Should` checks, timeouts, the `speed` pacing argument |
| `references/gestures-and-input.md` | taps, swipes, scrolling to an element, text input, the keyboard and key presses |
| `references/device-state.md` | permissions, location, orientation, dark and airplane mode, gallery media, screenshots, screen recording |
| `references/flows-and-studio.md` | `Run Flow`, recording flows with `record_flows`, converting YAML to Robot, Maestro Studio |
| `references/troubleshooting.md` | a device that stops answering, adb or Maestro errors, logcat and mirroring, iOS limits |

Examples in `assets/examples/`: `android-basic.robot`, `ios-basic.robot`, `device-state.robot`.

## Companion Skills

| Need | Skill |
|------|-------|
| Mobile app tests with AppiumLibrary | `rf-appium` (plugin `rf-mobile`) |
| Install Robot Framework or a library, fix the environment | `rf-setup` (plugin `rf-core`) |
| Write tests, suites, user keywords, resources and variables in Robot Framework syntax | `rf-language` (plugin `rf-core`) |

For running, discovering, keyword documentation, result analysis and debugging with the robotcode CLI, use the `robotcode` skill of the robotcode plugin (`robotcode@robotframework-agent-plugins`); the commands above work without it.
