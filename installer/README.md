# robotframework-plugins

Installs the Robot Framework plugins (skills, subagents and hooks for coding agents) into the folders each agent reads, for seven agents:

| Agent | What it gets |
|---|---|
| Claude Code | skills, subagents, hooks |
| GitHub Copilot (CLI and VS Code) | skills, subagents, hooks |
| OpenAI Codex | skills, TOML subagents, hooks (after you trust them with `/hooks`) |
| Cursor | skills, subagents, hooks |
| OpenCode | skills, subagents; edit validation, error hints and the environment report through its JS plugin |
| Project Goose | skills, plus the subagents folded into `.goosehints` |
| Claude Desktop | one upload-ready ZIP per skill (Customize → Skills → Upload a skill) |

This package was called `rf-agentskills` up to 0.8.0. That name now forwards here.

## Install

Run it without installing anything first:

```bash
uvx robotframework-plugins install        # or: pipx run robotframework-plugins install
```

In a terminal, `install` asks which agents to set up, with the ones found on your machine already selected. It installs `rf-core` plus the plugins for the libraries your `pyproject.toml` or `requirements*.txt` declares, into the current project.

### Choose the plugins

```bash
robotframework-plugins catalog                         # what's available, with tiers and versions
robotframework-plugins install --plugins rf-core,rf-web
robotframework-plugins install --plugins all           # every verified plugin
```

On an upgrade, `install` keeps the plugins that cover what's already installed and adds the ones your project now declares. Narrow the set with `--plugins`; the summary lists the skills and plugins it removed.

### Without prompts (CI, scripts)

No prompt appears when you pass an explicit selection, `--yes`, or when stdin isn't a terminal:

```bash
robotframework-plugins install --agents claude-code,cursor   # explicit list
robotframework-plugins install --agents all                  # every known agent
robotframework-plugins install --agents detected --yes       # only the agents found here
robotframework-plugins install --agent claude-code           # one agent
```

`--agents none` does nothing. With no agent found and no selection, the command exits non-zero and lists the valid agents.

### Project or user scope

Installs go into the current project by default (for example `./.claude/`), so they can be reviewed and committed. Use `--scope user` to install for every project under your home directory:

```bash
robotframework-plugins install --agents all                  # into ./<agent folders>
robotframework-plugins install --agents all --scope user     # into ~/<agent folders>
```

The installer records what it wrote in `<project>/.rf-agentskills/` (or a per-user data folder for user scope), so `uninstall` removes exactly its own files.

### Marketplace settings instead of files

For agents with a plugin marketplace, `--mode plugin` writes the marketplace settings instead of copying files, so updates come through the agent:

```bash
robotframework-plugins install --agent claude-code --mode plugin
robotframework-plugins install --agent claude-code --mode plugin --ref rf-core--v1.0.0   # pin a release
```

### Upgrading

Run `install` again with the same agent and scope. Files the previous install wrote that the new version no longer ships are removed when you haven't changed them; files you changed are kept and reported. `--dry-run` shows them as `remove` and `keep` rows first. An install made by `rf-agentskills` 0.8.0 or earlier is moved to the new layout the same way.

### Pre-releases

Pre-releases need an opt-in: `pipx install --pip-args=--pre robotframework-plugins`, `uv tool install --prerelease allow robotframework-plugins`, or an exact pin such as `robotframework-plugins==2026.12.0rc1`. If uv or pip can't find a release published the same day, refresh the index cache: `uv cache clean robotframework-plugins` or `pip install --no-cache-dir`.

## Commands

```
robotframework-plugins install   [--agents all|none|detected|<csv> | --agent <name> | --all]
                                 [--plugins <csv>|all] [--scope project|user] [--project DIR]
                                 [--mode files|plugin] [--ref TAG] [--what skills,agents,hooks]
                                 [--yes] [--no-input] [--dry-run] [--force]
robotframework-plugins uninstall --agent <name> [--scope project|user] [--project DIR]
robotframework-plugins catalog   [--json]   # the plugins this version bundles
robotframework-plugins list                 # what's installed where
robotframework-plugins targets              # which agents are found on this machine
robotframework-plugins doctor               # what works and what needs your attention
robotframework-plugins version              # this version and the bundled plugin versions
```

## No telemetry

The installer sends nothing anywhere. It only touches the network for the marketplace and package operations you ask for.

## More

The plugins, their tiers and the per-agent marketplace steps are described in the [repository README](https://github.com/MarketSquare/robotframework-plugins#readme). Releases and the version table: [RELEASING.md](https://github.com/MarketSquare/robotframework-plugins/blob/main/RELEASING.md).
