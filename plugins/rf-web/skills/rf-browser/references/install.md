# Installing Browser Library

Commands are in uv form. For a new environment, Poetry and venv + pip forms, and the general troubleshooting (wrong interpreter, PEP 668, old Python), see `rf-setup` (plugin `rf-core`): `uv add <pkg>` is `poetry add <pkg>` (pip alternative: `.venv/bin/python -m pip install <pkg>`), and `uv run <cmd>` is `poetry run <cmd>` or `.venv/bin/<cmd>`. Versions and floors checked on PyPI 2026-09-26.

Package `robotframework-browser` (20.x, Python ≥ 3.10). Module `Browser`. There are two ways to install it; both are verified.

## A. Without Node.js (recommended for agents): BrowserBatteries

```bash
uv add "robotframework-browser[bb]"
uv run rfbrowser install chromium          # ~115 MiB; omit "chromium" to get chromium, firefox and webkit (~700 MB)
```

The `[bb]` extra pulls `robotframework-browser-batteries`, which ships prebuilt Node binaries and dependencies. It may not exist for every OS/CPU. If the install finds no matching wheel, use B.

## B. With Node.js

```bash
node --version                              # Node 22, 24 or 26 LTS
uv add robotframework-browser
uv run rfbrowser init chromium              # installs the node dependencies + chromium
```

- Use `rfbrowser install` **only** with `[bb]`, and `rfbrowser init` **only** on the Node.js path. Don't mix them.
- If `rfbrowser` is not found: `uv run python -m Browser.entry install chromium` (`[bb]`), or `uv run python -m Browser.entry init chromium` on the Node.js path.
- Node 26 with npm 12 blocks post-install scripts. After the Node.js-path `rfbrowser init`, run `npm approve-scripts --allow-scripts-pending`, review the list, approve the packages, and run the Node.js-path init again.
- `--skip-browsers` skips the browser download when you manage Playwright browsers yourself.

Browser binaries are stored **inside the environment** (`site-packages/Browser/wrapper/…`). A new venv, or `uv sync` into a fresh `.venv`, needs the install step again. Run it again after upgrading Browser too.

## Verify

```bash
uv run robot --outputdir results tests/browser_smoke.robot
```

```robotframework
*** Settings ***
Library    Browser

*** Test Cases ***
Browser Opens A Page
    New Browser    chromium    headless=True
    New Page    data:text/html,<h1>ok</h1>
    Get Text    h1    ==    ok
```

## `rfbrowser` not found, or Browser not initialised

**Symptom:** `rfbrowser: command not found`, or tests fail with `Could not connect to the playwright process`, `Executable doesn't exist at …/chromium…`, or `Browser library … node dependencies are not installed`.
**Cause:** `rfbrowser` lives in the project environment's scripts folder and isn't on PATH, or the post-install step never ran for this environment (a fresh `.venv` has no browsers).
**Fix:** run it through the environment: `uv run rfbrowser install chromium` with `[bb]`. On the Node.js path, `uv run rfbrowser init chromium`. Fallback: `uv run python -m Browser.entry install chromium`.

## In CI

Add the browser step after `uv sync --locked` (GitHub Actions; `--with-deps` installs the OS libraries):

```yaml
      - name: Install Playwright browser (Browser[bb])
        run: uv run rfbrowser install chromium --with-deps
```

On the Node.js path, install Node first and run the Node.js-path init: `uv run rfbrowser init chromium`.

The browser binaries live inside `.venv`, so every job installs them; the uv cache doesn't cover them. For containers, the Browser project publishes images with browsers preinstalled (`ghcr.io/marketsquare/robotframework-browser/rfbrowser-stable`).

Add `playwright-log.txt` and `browser/` to `.gitignore`.
