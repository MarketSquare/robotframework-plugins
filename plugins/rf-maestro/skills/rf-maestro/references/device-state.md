# Device state, screenshots and recordings

Read this when a test changes the device or the app's permissions, location, orientation or appearance, or when it records or compares screens.

## Treat device state as test data

Set a state with a keyword, put it back in a teardown, and do not change it with `Execute Adb Shell` when a keyword exists. A state left behind breaks the next test.

| State | Keyword | Notes |
|---|---|---|
| App permissions | `Set Application Permissions    camera=deny    all=allow` | values are per permission; `all` covers the rest |
| Permissions at launch | `Open Application    <app id>    permissions=...` | without it, Maestro grants every runtime permission on launch |
| Clean app data | `Clear Application State` | wipes what the app stored; the signed-out start |
| Location | `Set Location    <lat>    <lon>` | `altitude` is accepted and ignored |
| Route | `Travel    <point>    <point>    speed=...` | moves the location along points |
| Orientation | `Landscape`, `Portrait`, `Set Orientation    LANDSCAPE_LEFT` | names as the library lists them |
| Dark mode | `Set Dark Mode    ${True}` | the device setting, not the app's own switch |
| Airplane mode | `Set Airplane Mode    ${True}` | Android only; iOS simulators have none |
| Gallery | `Add Media    <path>` | images or videos put into the gallery |

Undo each change in a teardown:

```robotframework
*** Test Cases ***
Read Landscape Layout
    [Teardown]    Portrait
    Landscape
    Expect Element    id=chart_view    visible
```

## Screenshots

- `Capture Page Screenshot    <name>` saves a JPEG as `maestro-screenshot-<n>.jpg` in the output folder. Pass `EMBED` as the name to put it in the log instead of a file.
- `Capture Element Screenshot    <locator>` saves one element as PNG.
- `Screenshot Should Match    <reference.png>` compares the screen with a reference image. `threshold` is the match percentage (default 95). Add `locator=` to compare one element only.

The import argument `run_on_failure` (default `Capture Page Screenshot`) saves a screenshot when a test fails. `Register Keyword To Run On Failure` changes that keyword for the rest of the test.

## Screen recording

- `Start Screen Recording` begins a recording; `time_limit` defaults to 3 minutes.
- `Stop Screen Recording    <filename>` saves the file under the name given. It does not add an extension.
- Both work on Android (through adb) and on the iOS simulator (through `xcrun simctl`).
- Maestro ends its own recording with each flow, and each keyword is its own flow. So start the recording in the test and put `Stop Screen Recording` in a teardown, so a failing test still saves its video.

## Shell access on Android

`Execute Adb Shell    <command>    <args...>    timeout=30s` runs one adb shell command on the device. It fails at once on iOS. Use it for what no keyword covers, and not for permissions, location, orientation or dark mode, which have keywords above.

## Logs

On Android the library streams `adb logcat` to `logcat/<n>-<test>.txt` in the output folder, for each test. Turn it off with the import argument `logcat=False`. Mirroring and the iOS log stream are in the troubleshooting notes listed in SKILL.md.
