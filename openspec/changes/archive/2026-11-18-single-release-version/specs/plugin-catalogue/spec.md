## MODIFIED Requirements

### Requirement: Shared files have one owner

A file used by more than one plugin SHALL live in one plugin. Every other plugin that needs it SHALL carry a copy that `scripts/build-catalog.py` generates and its `--check` keeps in step. A plugin SHALL NOT contain a symlink, because Codex drops symlinks when it installs a plugin (split-rf-agentskills design D5); the catalogue check SHALL fail on one and name it. The security gate SHALL treat a change to a shared file as a change to every plugin that carries a copy.

#### Scenario: Symlink in a plugin
- **WHEN** a plugin contains a symlink, whether it points inside or outside the repository
- **THEN** the catalogue check fails and names the link

#### Scenario: Shared hook change scans both plugins
- **WHEN** a PR changes a hook script that a second plugin carries a copy of
- **THEN** the security gate scans both plugins

### Requirement: Each installer release states what it bundles

The release notes, the README and `docs/catalog.md` SHALL name the release version and list the plugins the release contains, with their tiers. All of them carry the release version, so no per-plugin version column is needed.

#### Scenario: Release notes carry the table
- **WHEN** release `5.0.0` is published
- **THEN** its notes say that the installer and every listed plugin are at `5.0.0`, and list each bundled plugin with its tier
