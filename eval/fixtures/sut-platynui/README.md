# sut-platynui

Spec-only PlatynUI fixture (desktop automation over Windows UIA / Linux
AT-SPI2). The CI runner has no desktop session, so tasks on this fixture are
graded **statically** with `keywords_resolve` against the committed libdoc spec
`specs/PlatynUI.BareMetal.json` (PlatynUI 0.12.0.dev330).

## Application under test: Calculator

The standard desktop calculator (Windows Calculator / GNOME Calculator).

| Element | XPath (PlatynUI desktop tree) |
|---|---|
| Main window | `//control:Window[@Name='Calculator' or @Name='Rechner']` |
| Digit buttons | `//control:Button[@Id='num1Button']` … `//control:Button[@Id='num9Button']` |
| Plus / Equals | `//control:Button[@Id='plusButton']`, `//control:Button[@Id='equalButton']` |
| Result display | `//control:Text[@Id='CalculatorResults']` |

PlatynUI exposes the UIA AutomationId as `@Id`, as `rf-platynui` teaches; a
plain `@AutomationId` matches nothing. `@Name` values follow the display
language (a German desktop shows `Rechner`, `Eins`, `Gleich`), so the window
locator lists both names and the controls use `@Id`. The result display's
`Name` holds the shown value, such as "Display is 3" (localised). Verified with
`platynui-cli query` on Windows 11 on 2026-11-12.

`tests/example.robot` is a stub that resolves cleanly. Real execution stays a
manual, local activity on a desktop machine.

## Refreshing the spec

```bash
uv run python -m robot.libdoc PlatynUI.BareMetal eval/fixtures/sut-platynui/specs/PlatynUI.BareMetal.json
```
