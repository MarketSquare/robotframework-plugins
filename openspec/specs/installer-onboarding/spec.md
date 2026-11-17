# installer-onboarding Specification

## Purpose

Make the `rf-agentskills` installer approachable and automation-friendly: it presents an interactive selection wizard on a terminal, runs fully headless when given an explicit selection or in non-interactive contexts, defaults to project scope with user scope as an explicit opt-in, and is reachable as a zero-install PyPI entry point for `uvx`/`pipx run` usage.

## Requirements

### Requirement: Bare install is interactive in a terminal

The installer SHALL present a selection wizard rather than erroring when `rf-agentskills install` is run with no explicit agent selection in an interactive terminal.

#### Scenario: Wizard offered on a TTY
- **WHEN** `rf-agentskills install` runs with stdin attached to a TTY and no `--agent`/`--all`/`--agents`/`--yes`
- **THEN** a multi-select of all known agents is shown
- **AND** agents detected on the machine are pre-selected
- **AND** the resolved scope and target directory are shown for confirmation before any file is written

#### Scenario: Wizard works without the optional extra
- **WHEN** the `[interactive]` extra (questionary) is not installed but the session is interactive
- **THEN** the installer falls back to a stdlib numbered selector
- **AND** still never requires the extra to complete an install

### Requirement: Installer is fully runnable without user input

The installer SHALL complete any install or uninstall without prompting when
given an explicit selection, when `--yes` is passed, or when stdin is not a
TTY. No code path SHALL block on input in a non-interactive context.

#### Scenario: Explicit agent list is headless
- **WHEN** `rf-agentskills install --agents claude-code,cursor` runs with stdin redirected from `/dev/null`
- **THEN** it installs into exactly those agents and exits 0 with no prompt

#### Scenario: all / none / detected selectors
- **WHEN** `--agents all`, `--agents none`, or `--agents detected` is passed
- **THEN** the selection resolves to every known agent, an empty set (no-op, exit 0), or only machine-detected agents respectively, with no prompt

#### Scenario: Non-TTY falls back to detected
- **WHEN** `rf-agentskills install` runs with no selection and stdin is not a TTY
- **THEN** it installs into the detected agents without prompting
- **AND** if no agent is detected it exits non-zero and prints the list of valid agents and the flag to use

#### Scenario: Back-compat flags still work
- **WHEN** the existing `--agent <name>` or `--all` flags are used
- **THEN** they behave as before (single agent / every detected agent) with no prompt

### Requirement: Project scope is the default, user scope is opt-in

Installs SHALL default to project scope, writing into the current directory's
per-agent config; `--scope user` SHALL be required to perform a global
(home-directory) install.

#### Scenario: Default writes into the project
- **WHEN** `rf-agentskills install --agents claude-code` runs with no `--scope`
- **THEN** files are written under the current directory (e.g. `./.claude/...`), not under `~`
- **AND** `--project` defaults to the current working directory

#### Scenario: User scope still available
- **WHEN** `--scope user` is passed
- **THEN** the install targets the home-directory layout (e.g. `~/.claude`) as before

### Requirement: Zero-install entry point via PyPI

The `robotframework-plugins` package SHALL be published to PyPI so it can be run without a prior install, mirroring `npx`-style usage. Releases SHALL be published from the release workflow with PyPI trusted publishing (GitHub OIDC) from a protected `pypi` environment, without a long-lived PyPI token. The final `rf-agentskills` release SHALL forward to it, as `repository-migration` defines.

#### Scenario: uvx / pipx run works
- **WHEN** a user runs `uvx robotframework-plugins install` (or `pipx run robotframework-plugins install`)
- **THEN** the published package resolves from PyPI and the installer runs

#### Scenario: Release publishes without a stored token
- **WHEN** an installer release tag `robotframework-plugins-v<version>` is pushed and a maintainer approves the `pypi` environment
- **THEN** the wheel and sdist for `<version>` are published to PyPI through trusted publishing, and the repository has no PyPI token secret

### Requirement: Installer versions are calendar versions

`robotframework-plugins` SHALL use versions of the form `YYYY.M.PATCH` without zero padding: the year and month of the release, and a patch number that starts at 0 each month. The release tag SHALL be `robotframework-plugins-v<version>`, and the release workflow SHALL fail when the tag's year and month don't match the release date or the version in `installer/pyproject.toml`. A breaking change to the CLI SHALL be announced in the changelog of the release before it lands.

#### Scenario: Second release in a month
- **WHEN** `2026.12.0` was released and a fix is released later in December 2026
- **THEN** its version is `2026.12.1`

#### Scenario: Wrong month fails
- **WHEN** a tag `robotframework-plugins-v2026.11.0` is pushed in December 2026
- **THEN** the release workflow fails before publishing and states the expected `2026.12.<n>`
