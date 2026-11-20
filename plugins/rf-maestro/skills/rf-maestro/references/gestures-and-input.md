# Taps, swipes, scrolling and text input

Read this when a test taps, swipes, scrolls to an element, types into a field, or hides the keyboard.

## Taps

| Keyword | Use |
|---|---|
| `Tap    <locator>` | one tap on the element |
| `Tap    <locator>    count=2` | a repeated tap (double tap) |
| `Long Press    <locator>` | a long press on the element |
| `Click Element    <locator>` | a tap that reads like AppiumLibrary's `Click Element` |
| `Click Text    <text>` | a tap on the element whose text contains the string; `exact_match=True` for the whole text |
| `Click Alert Button    <button name>` | a button on a system alert (iOS is not tested yet) |

## Swipes

`Swipe` takes pixel coordinates by name. Its arguments are keyword-only:

```robotframework
Swipe    start_x=500    start_y=1500    end_x=500    end_y=400    duration=300ms
```

- `duration` takes a time string (`300ms`, `1s`). A bare number is milliseconds.
- `Swipe By Percent    <start x %>    <start y %>    <end x %>    <end y %>` works on screen size, so one test runs on phones of different sizes.
- `Travel` moves the device location along a list of points. It is listed with the other device-state keywords in SKILL.md.

## Scrolling

- `Scroll Down    <locator>` and `Scroll Up    <locator>` swipe until the element is visible, or fail after `timeout` (default 10 seconds).
- `x=<percent>` swipes along one column of the screen instead of the middle. Use it on a screen with a map, signature pad or canvas in the middle, where a swipe would draw instead of scroll. With `x`, the scroll also stops early when the screen stops changing, which means the end of the content.
- `Scroll Element Into View    <locator>` scrolls until the locator is on screen.

```robotframework
Scroll Down    id=terms_accept_button    x=2
Tap            id=terms_accept_button
```

## Text input

| Keyword | Use |
|---|---|
| `Input Text    <locator>    <text>` | tap the element, then type into it |
| `Input Password    <locator>    <password>` | the same, and the text is never logged |
| `Input Text Into Current Element    <text>` | type into the element that already has focus |
| `Clear Text    <locator>` | empty a field |

Keep credentials in a variable from the environment file (`%{APP_PASSWORD}`), and type them with `Input Password`.

## Keyboard and keys

- `Hide Keyboard` hides the on-screen keyboard. On iOS, pass `key_name=Done` to dismiss it with the keyboard's own key.
- `Is Keyboard Shown` returns true or false. It is Android only.
- `Press Key    <key>` sends a Maestro key name, for example `Enter`, `Backspace`, `Home`, `Tab`, `Volume Up`, `Escape`. `Back`, `Power` and `Tab` are Android keys.
- `Press Keycode    <number>` sends an Android keycode number, for AppiumLibrary suites that already use keycodes. It is Android only.

## Common mistakes

- A swipe with no `duration` is one second. Set `duration` for a quick flick (`200ms`) or a slow drag (`1s`) when the app reacts to speed.
- Do not add `Sleep` to let suggestions load. Wait for the suggestion with `Wait Until Page Contains`.
