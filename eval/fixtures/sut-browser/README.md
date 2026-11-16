# sut-browser

Browser-library Robot Framework project. Ships a small static HTML login page
at `pages/login.html` that the tests load via a `file://` URL, so there's no
external web dependency.

## Setup

Install deps and then initialize Playwright browsers:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
rfbrowser init     # downloads Playwright browser binaries (~400 MB first run)
```

**Important:** `rfbrowser init` must be run **after** installing
`robotframework-browser`.

## Smoke test

```bash
robot tests/example.robot
```
