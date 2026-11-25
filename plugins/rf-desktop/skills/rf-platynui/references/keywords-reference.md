# PlatynUI.BareMetal — Keyword Reference

Complete keyword surface of `Library    PlatynUI.BareMetal` (verified against `robotframework-PlatynUI==0.14.0.dev0`, library version `0.14.0-dev.0`, scope `SUITE`, doc format `ROBOT`). **32 keywords, all documented.**

> The high-level `PlatynUI` library is a placeholder (`Dummy Keyword` only). Use `BareMetal`.

## Import

```robotframework
Library    PlatynUI.BareMetal
...    keyboard_profile=${None}     # KeyboardProfileLike | dict | None
...    pointer_settings=${None}     # PointerSettingsLike | dict | None
...    pointer_profile=${None}      # PointerProfileLike  | dict | None
...    use_mock=${False}            # mock provider (needs --features mock-provider build)
...    auto_activate=${True}        # foreground target window before pointer/keyboard
...    query_settings=${None}       # wait defaults, e.g. {'timeout': 60}
...    config=${None}               # session binding, e.g. {'platform': {'x11': {'display': ':1'}}}
...    native_log_level=${None}     # PlatynUI's own log level (default warn)
```

All import args are keyword-only and optional.

## Element references

Most keywords take a `descriptor: UiNodeDescriptor` — pass either:
- a **PlatynUI XPath string** (e.g. `//control:Button[@Name="OK"]`) — auto-converted, lazily resolved with retry (30 s by default) until the node appears or `ElementNotFoundError` is raised, or
- a **`UiNode`** captured from `Query ... only_first=${True}`.

Where the signature shows `descriptor: ... | None`, passing `${None}` means "no element" (act on raw coordinates, or type into whatever currently has focus).

Every keyword that takes a descriptor also takes a keyword-only `query_overrides: QuerySettingsDict | None = None`, for example `query_overrides={'timeout': 10}`, which tunes the wait for that call only (see Waiting).

## Query & scope

| Keyword | Arguments | Returns | Notes |
|---------|-----------|---------|-------|
| `Query` | `expression: str`, `root: UiNode \| None = None`, `only_first: bool = False` | node / list / value | Evaluate an XPath expression. `only_first=${True}` → first `UiNode` or `${None}`. Value expressions (`count(...)`) return the computed value. Read-only. |
| `Set Root` | `descriptor: UiNodeDescriptor \| None`, `scope='LOCAL'` | previous root | Scope subsequent queries to a subtree. `${None}` resets to the desktop. `scope` is `LOCAL`/`TEST`/`TASK`/`SUITE`/`SUITES`/`GLOBAL`. |
| `Get Element At Point` | `x: float`, `y: float` | node or `${None}` | The element under a screen point. Does not wait. |

## Pointer / mouse

Shared optional args (keyword-only `*`): `button: PointerButtonLike = LEFT` (`LEFT`/`MIDDLE`/`RIGHT` or `1`/`2`/`3`), `x`/`y: float | None`, `overrides: PointerOverridesLike | None`, `activate: bool | None` (defaults to library `auto_activate`). See coordinate rules in SKILL.md.

| Keyword | Arguments | Short doc |
|---------|-----------|-----------|
| `Pointer Click` | `descriptor=None`, `*`, `button=LEFT`, `x=None`, `y=None`, `overrides=None`, `activate=None` | Click at absolute or element-relative screen coordinates. |
| `Pointer Multi Click` | …above… `+ clicks: int = 2` | Multiple clicks (double=`${2}`, triple=`${3}`). |
| `Pointer Press` | same as Pointer Click | Press (and hold) a mouse button. |
| `Pointer Release` | same as Pointer Click | Release a mouse button at current or specified coordinates. |
| `Pointer Move To` | `descriptor=None`, `*`, `x=None`, `y=None`, `overrides=None`, `activate=None` | Move the pointer (no `button`). |
| `Pointer Scroll` | `descriptor=None`, `*`, `direction='DOWN'`, `ticks: int = 1`, `x=None`, `y=None`, `overrides=None`, `activate=None` | Turn the mouse wheel over an element, at coordinates, or (`${None}`, no x/y) where the pointer is. `direction` is `UP`/`DOWN`/`LEFT`/`RIGHT`; one tick is one wheel notch. |
| `Get Pointer Position` | `assertion_operator=None`, `assertion_expected=None`, `assertion_message=None` | Current pointer position (assertable). |

## Keyboard

| Keyword | Arguments | Short doc |
|---------|-----------|-----------|
| `Keyboard Type` | `descriptor: UiNodeDescriptor \| None`, `text: str \| Secret`, `*`, `overrides: KeyboardOverridesLike \| None = None`, `activate=None` | Type a sequence of characters and/or keys (full press→release). |
| `Keyboard Press` | `descriptor \| None`, `text: str \| Secret`, `*`, `overrides=None`, `activate=None` | Press (and hold) keys. |
| `Keyboard Release` | `descriptor \| None`, `text: str \| Secret`, `*`, `overrides=None`, `activate=None` | Release keys. |

`descriptor` is positional but may be `${None}` (skip focusing). Key syntax: `<Ctrl+A>`, `<Return>`, `<ESC>`, `<Shift+Tab>`, plain text, `${\n}`. A literal `<` is `\\<` in test data (Robot Framework removes one backslash). List valid key names: `platynui-cli keyboard list`.

## Focus & attributes

| Keyword | Arguments | Short doc |
|---------|-----------|-----------|
| `Focus` | `descriptor: UiNodeDescriptor`, `*`, `activate=None` | Set keyboard focus to the element, raising its window first (`activate=${False}` skips that). |
| `Bring To Front` | `descriptor: UiNodeDescriptor` | Bring the element's window to the front and give it the keyboard focus. |
| `Get Attribute Value` | `descriptor`, `attribute_name: str`, `assertion_operator=None`, `assertion_expected=None`, `assertion_message=None` | Read one attribute once (assertable). Name it bare (`Name`, `IsEnabled`, `Bounds`); `app:`/`native:` prefixes select those namespaces. The value is typed (`IsEnabled` a boolean, `Bounds` a `Rect`). |
| `Get Attribute` | same as `Get Attribute Value` | **Deprecated** alias of `Get Attribute Value`, to be removed before PlatynUI 1.0. Don't use it. |

`Get Attribute Value` is **assertable** — `Get Attribute Value  //control:Button[@Name="OK"]  Name  ==  OK`. It reads and checks once; to wait until a value holds, use `Wait Until Attribute Value`. Typed/structured attributes expose component aliases (`Bounds.X`, `Bounds.Width`, `ActivationPoint.Y`).

## Window surface

All take `descriptor: UiNodeDescriptor` and require a window node (else `PatternError`).

| Keyword | Extra args | Short doc |
|---------|-----------|-----------|
| `Activate Window` | — | Activate (bring to front and focus) a window. |
| `Bring To Front` | — | (listed above — front with focus) |
| `Minimize Window` | — | Minimize a window. |
| `Maximize Window` | — | Maximize a window. |
| `Restore Window` | — | Restore from minimized/maximized. |
| `Close Window` | — | Close a window. |
| `Move Window` | `x: float`, `y: float` | Move top-left to screen coordinates. |
| `Resize Window` | `width: float`, `height: float` | Resize. |
| `Move And Resize Window` | `x`, `y`, `width`, `height` (float) | Move + resize in one operation. |

## Waiting

Action and read keywords already wait for their target. These wait without acting; each returns once its condition holds, or fails when `timeout` elapses.

| Keyword | Arguments | Short doc |
|---------|-----------|-----------|
| `Wait Until Exists` | `descriptor`, `*`, `query_overrides=None` | Wait until a selector resolves to an element; returns it. Fails with `ElementNotFoundError`. |
| `Wait Until Gone` | `descriptor`, `*`, `query_overrides=None` | Wait until a selector matches nothing, or a captured element is no longer valid. Fails with `ElementStillPresentError`. |
| `Wait Until Attribute Value` | as `Get Attribute Value`, `*`, `query_overrides=None` | Wait until an attribute satisfies the assertion; returns the value. |
| `Wait Until Query` | `expression: str`, `assertion_operator=None`, `assertion_expected=None`, `assertion_message=None`, `*`, `root=None`, `query_overrides=None` | Wait until an XPath result satisfies the assertion (default: until it is truthy), e.g. `count(...)    >    ${0}`. |
| `Set Query Settings` | `overrides: QuerySettingsDict \| None = None`, `scope='LOCAL'` | Set the wait for a Robot Framework scope, like `Set Root`; it clears itself when the scope ends (except `GLOBAL`). |

The query settings are `timeout` (default `30` s), `retry_interval` (default `0.1` s) and `ignore_exceptions` (default `False`). The most specific level wins: `query_overrides=` on one call, then `Set Query Settings` for a scope, then `query_settings=` at library import.

## Diagnostics

| Keyword | Arguments | Short doc |
|---------|-----------|-----------|
| `Take Screenshot` | `descriptor=None`, `filename='platynui-screenshot-{index}.png'`, `rect: RectLike \| None = None` | Full screen, an element (its bounds), or a rect. `filename=EMBED` embeds base64 PNG in the log; files go to `${OUTPUT DIR}`; `{index}` auto-increments. |
| `Highlight` | `descriptor: ... \| list \| None = None`, `*`, `rect: RectLike \| list \| None = None`, `duration: float = 1.0` | Draw an overlay around one/many elements or rect(s) for `duration` seconds. Needs at least one of descriptor/rect. |

## Not present (know the gaps)

- **No application launch/attach keyword** — launch with `Library Process` (`Start Process    calc.exe`) and locate via `app:Application[...]`.
- **No semantic action keywords** (`Activate`, `Select`, `Set Value`, `Check`) — these are the *intended direction* of the high-level library, not shipped. Compose `Pointer Click` / `Keyboard Type` / `Query` instead. See `status-and-migration.md`.

## Types referenced

- `PointerButtonLike` = `PointerButton` enum (`LEFT=1`, `MIDDLE=2`, `RIGHT=3`) or `int`.
- `RectLike` = `Rect` | `(x, y, width, height)` tuple | `{x, y, width, height}` dict.
- `*OverridesLike` / `*ProfileLike` / `*SettingsLike` = native object or a `&{dict}` (keys like `press_delay_ms`, `between_keys_delay_ms`, `acceleration_profile`, `motion`, `jitter_amplitude`, `multi_click_delay_ms`).
- Exceptions: `BareMetalError` → `ElementNotFoundError`, `ResultTypeError`, `NoQueryError`; native `PlatynUiError` → `PatternError`, `PointerError`, `KeyboardError`, `ProviderError`, …
