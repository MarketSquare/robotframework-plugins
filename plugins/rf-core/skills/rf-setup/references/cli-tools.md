# Standalone CLI Tools: `uv tool`, `uvx`, `pipx`

`uv tool install`, `uvx` and `pipx` put a command-line tool into **its own isolated environment** and link the command onto PATH. That is right for tools that don't need to import your test libraries, and wrong for everything `robot` needs at run time.

| Use a tool environment for | Keep in the project environment |
|---|---|
| `robotframework-plugins` (the installer for these skills) | `robotframework` |
| `uv` itself (`pipx install uv`) | Every test library (Browser, SeleniumLibrary, RequestsLibrary, …) |
| optional CLIs a library skill names (it gives the command) | `robotcode[all]` (it imports your libraries for `doc`, `discover`, `analyze`; never `uvx robotcode`) |
| One-off commands: `uvx robotframework-plugins install` | `robocop` (comes with `robotcode[all]`; uses the project's RF version) |

Why: a library installed with `pipx install robotframework-browser` lives in `~/.local/pipx/venvs/robotframework-browser/`. Your project's `robot` can't import it, so you get `No module named 'Browser'` or `Importing library 'Browser' failed`.

## Commands

```bash
# uv
uv tool install robotframework-plugins  # persistent, on PATH
uvx robotframework-plugins install      # run once without installing
uv tool upgrade robotframework-plugins
uv tool list

# pipx
pipx install robotframework-plugins
pipx run robotframework-plugins install
pipx upgrade robotframework-plugins
```

Pre-release tools need an opt-in: `uv tool install --prerelease allow <tool>`, `pipx install --pip-args=--pre <tool>`.

## Hooks and the installer

The rf-core hooks (validation, environment check) run Python. The installer records the interpreter it was installed with in `python_runtime.json`, and the hooks prefer it. If hooks report "robotframework not installed" although the project has it, the hooks are using a different interpreter than the project. Install `robotcode[all]` into the project env (see the robotcode step in SKILL.md), or rerun the installer from inside the project env: `uv run robotframework-plugins install` after `uv add --dev robotframework-plugins`.
