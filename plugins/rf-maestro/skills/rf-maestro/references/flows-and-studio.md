# Maestro flows, conversion and Studio

Read this when a Maestro YAML flow must run from Robot, when a flow must become a Robot test, or when a test is recorded on a live device.

## Run a flow from a test

`Run Flow` runs a Maestro flow for the commands that have no keyword:

| Form | Example |
|---|---|
| a flow file | `Run Flow    ${CURDIR}/flows/onboarding.yaml    USER=demo` |
| a directory | `Run Flow    ${CURDIR}/flows/    include_tags=smoke    exclude_tags=slow` |
| inline YAML | `Run Flow    - tapOn:\n    text: Next` (a flow without a config section gets the current app's `appId`) |

- Named arguments become flow environment variables, read in the flow as `${NAME}`.
- `include_tags` and `exclude_tags` select flows by their `tags`, and are only valid with a directory. Pass several tags as a list variable, such as `@{TAGS}`.
- Flow paths in the file resolve next to the file, so `runFlow` and `runScript` calls keep working.

## Record the commands a test sends

Import with `record_flows=True`, and every Maestro command the test sends is written to `flows/<n>-<test>.yaml` in the output folder:

```robotframework
*** Settings ***
Library    MaestroLibrary    timeout=10s    record_flows=True
```

Run the test once, then copy the YAML that matches the steps you want to keep. Keep the recording out of version control if it holds credentials.

## Convert a flow to a Robot test

The converter needs the `convert` extra (PyYAML):

```bash
uv add "robotframework-maestrolibrary[convert]"
python -m MaestroLibrary.flow2robot settings_search.yaml > settings_search.robot
```

The output is a Robot suite. Review it before use: check each keyword it writes against `robotcode doc keyword MaestroLibrary` and run the suite once.

## Maestro Studio: record on a live device

Studio shows the device screen in a window. Each action you take on the screen runs on the device and adds the matching Robot line.

```bash
uv add "robotframework-maestrolibrary[studio]"        # PySide6, PyAV and grpcio
python -m MaestroLibrary.studio --app com.android.settings
```

Studio needs the Maestro CLI, adb and scrcpy on the machine, the same as the library.
## Maestro CLI commands

The library talks to `maestro mcp`. Keyword coverage of the other Maestro subcommands is in the library's `docs/maestro-cli.md`, in the project repository linked from the library's README.
