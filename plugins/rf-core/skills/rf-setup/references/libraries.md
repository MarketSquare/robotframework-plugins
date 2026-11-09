# Installing Test Libraries and Tools

Package names and where each library's install steps live. Versions and floors checked on PyPI 2026-09-26. Commands are shown in the uv form; the equivalents are:

| uv | Poetry | venv + pip |
|---|---|---|
| `uv add <pkg>` | `poetry add <pkg>` | `.venv/bin/python -m pip install <pkg>` (+ add it to `requirements.txt`) |
| `uv add --dev <pkg>` | `poetry add --group dev <pkg>` | same, in `requirements-dev.txt` |
| `uv run <cmd>` | `poetry run <cmd>` | `.venv/bin/<cmd>` or activated venv |

A quick import check works for any library: `uv run python -c "import <Module>"` (module names below).

## Robot Framework

- Package `robotframework` (7.5, Python ≥ 3.8). Module `robot`.
- Verify: `uv run robot --version` (exit code 251 is normal).

## Test libraries

Each library's skill has its install command, post-install steps and verification, in its `references/install.md`. If the skill isn't available, suggest installing its plugin.

| Library | Package | Module | Skill (plugin) |
|---|---|---|---|
| Browser (Playwright) | `robotframework-browser` | `Browser` | `rf-browser` (plugin `rf-web`) |
| SeleniumLibrary | `robotframework-seleniumlibrary` | `SeleniumLibrary` | `rf-selenium` (plugin `rf-web`) |
| AppiumLibrary | `robotframework-appiumlibrary` | `AppiumLibrary` | `rf-appium` (plugin `rf-mobile`) |
| RequestsLibrary | `robotframework-requests` | `RequestsLibrary` | `rf-requests` (plugin `rf-api`) |
| RESTinstance | `RESTinstance` | `REST` | `rf-restinstance` (plugin `rf-api`) |
| PlatynUI (preview) | `robotframework-PlatynUI` | `PlatynUI` | `rf-platynui` (plugin `rf-desktop`) |

## robotcode (required)

- Package `robotcode[all]>=2.8` (Python ≥ 3.10). Install as a **dev dependency in the project env**, never with `pipx`, `uvx` or `uv tool`: it imports your libraries. The `[all]` extra also installs Robocop (`robotframework-robocop>=6`), so Robocop needs no separate install.
- uv: `uv add --dev "robotcode[all]>=2.8"` · Poetry: `poetry add --group dev "robotcode[all]>=2.8"` · pip: `pip install "robotcode[all]>=2.8"`.
- Verify: `uv run robotcode discover info` shows the project's `.venv` Python; `uv run robocop --version` works.
- The rf-core validation hooks run `robotcode analyze code` (errors) and Robocop (deprecations, formatting) from the project environment.

## Other common packages

| Package | Use |
|---|---|
| `robotframework-pabot` | Parallel execution (`pabot` command) |
| `robotframework-datadriver` | Data-driven tests from CSV/Excel |
| `robotframework-databaselibrary` | SQL databases (plus a DB driver package) |
| `robotframework-sshlibrary` | SSH / SFTP |

Standard libraries (BuiltIn, Collections, String, OperatingSystem, Process, DateTime, XML, …) ship with Robot Framework. Nothing to install.
