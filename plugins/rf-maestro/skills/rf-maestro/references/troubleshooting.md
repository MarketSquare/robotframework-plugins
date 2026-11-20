# Troubleshooting MaestroLibrary runs

Read this when a run fails before a test starts, when the device stops answering, or when a keyword works on Android and fails on iOS.

## Import arguments

| Argument | Default | Use |
|---|---|---|
| `timeout` | `5s` | default wait for `Wait Until` and `Expect` keywords |
| `run_on_failure` | `Capture Page Screenshot` | keyword run when a test fails |
| `device` | first connected device | a device id such as `emulator-5554` |
| `maestro` | `maestro` | the Maestro CLI, when it is not on PATH under that name |
| `speed` | `0s` | pause before every Maestro command, for example `0.5s` |
| `logcat` | `True` | stream `adb logcat` per test to `logcat/<n>-<test>.txt` |
| `mirror` | `False` | show the Android device in a scrcpy window for the whole run |
| `record_flows` | `False` | write each test's commands to `flows/<n>-<test>.yaml` |

## Error messages

| Message | Cause | Fix |
|---|---|---|
| `Device '...' is not connected` | no emulator, device or simulator is up, or the `device=` id does not match | start it, then run `adb devices` (Android) or `xcrun simctl list devices booted` (iOS) |
| `adb did not run: install Android platform-tools` | adb is not on PATH | install platform-tools and put `adb` on the absolute PATH |
| `Physical iOS devices are not yet supported` | a physical iPhone was connected | use a simulator |
| `needs an Android device; Maestro has no iOS equivalent` | an Android-only keyword on iOS | see the table below |
| `Locator strategy '...' is not supported by Maestro` | an Appium-only locator prefix | rewrite with `id=`, `text=` or `regex=` |
| `did not match any elements` | a `Should` or `Get` keyword ran before the screen was ready | add `Wait Until Page Contains Element` or use `Expect Element` |

Open Application only warns when adb is missing, and returns as soon as Maestro does. Without adb, the app may not have window focus yet when the next step runs; install adb to make that wait work.

## Android-only and iOS-only keywords

| Keyword | Android | iOS simulator |
|---|---|---|
| `Go Back`, `Press Key    Back`, `Press Keycode` | yes | no: iOS has no back button |
| `Set Airplane Mode` | yes | no: simulators have none |
| `Execute Adb Shell`, `Is Keyboard Shown` | yes | no |
| `Start Screen Mirroring`, `Stop Screen Mirroring` | yes (scrcpy) | no: the Simulator window already shows the screen |
| `Kill Application`, `Clear Keychain` | yes | yes (both measured on a simulator) |

On iOS, `Hide Keyboard    key_name=Done` dismisses the keyboard. `Click Alert Button` has not been tested on iOS yet.

## A device that stops answering

Long runs can leave an emulator slow or unresponsive. Work through these in order:

1. Check the device with `adb devices`. A device that is not listed as `device` is not ready; restart the emulator before the run.
2. Add pacing with `speed=0.5s` on the import. Pacing is the first fix; lowering it makes the problem worse.
3. Give the emulator less RAM than the host has free, and keep the screen awake for physical devices.
4. Set a longer `timeout` for slow screens, or call `Set Maestro Timeout` for the Maestro commands.
5. Rerun the failed tests on a clean device. Count only the rerun, and report the first run as a setup failure when the cause was the device.

## Logs and mirroring

- Per-test logcat files appear in the output folder under `logcat/`. Check them first for an app crash.
- `Start Screen Mirroring` or `mirror=True` shows the Android screen with scrcpy. It needs a display.
- On iOS, the per-test log files stream the simulator's log (`xcrun simctl spawn <udid> log stream`).

## Slow runs

Do not add `Sleep` to fix a slow run. Use the wait keywords in SKILL.md, and the `timeout` and `speed` settings above.
