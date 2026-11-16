# Libdoc specs (keywords_resolve)

Libdoc JSON specs for libraries that can't run on the CI runner. The
`keywords_resolve` check of the PlatynUI and AppiumLibrary tasks resolves the
agent's keyword calls against them (`spec_dir: eval/graders/specs`). They are
**never staged into the agent's workspace**: the agent checks keywords against
the installed library, as it would in a real project.

| Spec | Library version | Tasks |
|---|---|---|
| `AppiumLibrary.json` | AppiumLibrary 3.2.1 | `*-appium-*` (rf-mobile) |
| `PlatynUI.BareMetal.json` | PlatynUI 0.12.0.dev330 | `*-platynui-*` (rf-desktop) |

Keep the versions equal to the ones in `uv.lock`. Refresh with:

```bash
uv run python -m robot.libdoc AppiumLibrary eval/graders/specs/AppiumLibrary.json
uv run python -m robot.libdoc PlatynUI.BareMetal eval/graders/specs/PlatynUI.BareMetal.json
```

A refreshed spec doesn't change the task hash; re-run the affected tasks to
check their baselines still hold.
