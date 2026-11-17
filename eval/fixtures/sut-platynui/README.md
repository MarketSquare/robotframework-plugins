# Calculator desktop tests

Robot Framework tests for the standard desktop calculator (Windows Calculator /
GNOME Calculator), automated with PlatynUI (Windows UIA / Linux AT-SPI2).

## Calculator elements

| Element | XPath (PlatynUI desktop tree) |
|---|---|
| Main window | `//control:Window[@Name='Calculator' or @Name='Rechner']` |
| Digit buttons | `//control:Button[@Id='num1Button']` … `//control:Button[@Id='num9Button']` |
| Plus / Equals | `//control:Button[@Id='plusButton']`, `//control:Button[@Id='equalButton']` |
| Result display | `//control:Text[@Id='CalculatorResults']` |

PlatynUI exposes the UIA AutomationId as `@Id`; a plain `@AutomationId`
matches nothing. `@Name` values follow the display language (a German desktop
shows `Rechner`, `Eins`, `Gleich`), so the window locator lists both names and
the controls use `@Id`. The result display's `Name` holds the shown value, such
as "Display is 3" (localised). Verified with `platynui-cli query` on Windows 11.

The tests need a desktop session with Calculator running:

```bash
uv run robot tests
```
