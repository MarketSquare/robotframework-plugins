# Install and verify MaestroLibrary

Read this when installing the library, the Maestro CLI, adb or Java, or when a check below fails.

## Requirements

| Part | Version | Check |
|---|---|---|
| Python | 3.12 or newer | `python --version` |
| Robot Framework | 7.5 or newer (installed with the library) | `python -m robot --version` |
| Maestro CLI | on PATH | `maestro --version` |
| Java | 17 or newer (Maestro needs it) | `java -version` |
| adb (Android) | platform-tools on PATH | `adb version` |
| Xcode (iOS) | macOS with a simulator | `xcrun --version` |

Optional: scrcpy on PATH and a display, for screen mirroring.

## Install the library

```bash
uv add robotframework-maestrolibrary
```

Extras:

- `robotframework-maestrolibrary[convert]` adds `pyyaml`, for `python -m MaestroLibrary.flow2robot`.
- `robotframework-maestrolibrary[studio]` adds PySide6, PyAV and grpcio, for `python -m MaestroLibrary.studio`.

## Where the tools must be

The library takes `maestro`, `adb`, `scrcpy` and `xcrun` only from absolute PATH folders. It never uses the working folder. Each tool must also answer like the real tool:

- `adb version` must print `Android Debug Bridge version <n>`;
- `xcrun --version` must print `xcrun version <n>`;
- `maestro mcp` must name itself `maestro`.

Anything else is refused. A tool that is installed under another name, or a wrapper script in the project folder, shows up as this refusal.

## Verify the install

Run these from the project environment:

```bash
python -c "import MaestroLibrary; print(MaestroLibrary.__version__)"
robotcode doc keywords MaestroLibrary
```

The first line prints the installed version. The second lists the library keywords, which are the names the tests may use.

## Android device

1. Start an emulator, or connect a device with USB debugging on.
2. Run `adb devices`; the device must show as `device`, not `unauthorized` or `offline`.
3. Pass `device=emulator-5554` to the import when more than one device is attached.

## iOS simulator

Maestro 2.11.0 drives iOS simulators only (macOS with Xcode). Physical iPhones fail with "Physical iOS devices are not yet supported". Boot a simulator, then open the app on it. The library does not need Appium or WebDriverAgent.
