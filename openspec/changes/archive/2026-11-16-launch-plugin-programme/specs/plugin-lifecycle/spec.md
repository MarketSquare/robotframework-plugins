## Purpose

Defines who owns each plugin, what maintainers commit to, and how a plugin is deprecated, demoted or removed, so that plugins nobody maintains do not linger in the catalogue.

## ADDED Requirements

### Requirement: Maintainer expectations are written down

`GOVERNANCE.md` SHALL state what plugin maintainers commit to:
- a first response to issues labelled for their plugin within 14 days;
- a first response to security reports within 7 days;
- a compatibility check of their plugin within 60 days of each Robot Framework major release, and of each major release of a library listed in `catalog.yaml`.

#### Scenario: Expectations are findable
- **WHEN** a prospective maintainer reads `GOVERNANCE.md`
- **THEN** it lists the three response targets with their durations

### Requirement: Deprecation before removal

A plugin SHALL be removed only after it has been `deprecated` for at least two installer releases and at least 90 days. Deprecating a plugin SHALL set `status: deprecated`, `deprecated_since` and `replacement` in `catalog.yaml`, add a deprecation notice to the top of the plugin's README, and be listed in the release notes. Removing a plugin SHALL be listed in the release notes of the installer release that stops bundling it, SHALL map its name to `null` in the marketplace `renames` map, and installer upgrades SHALL remove the plugin's installed files. Claude Code removes it through `forceRemoveDeletedPlugins`.

#### Scenario: Removal too early
- **WHEN** a PR sets `status: removed` for a plugin deprecated one release ago
- **THEN** the lifecycle check fails and states the earliest allowed release and date

#### Scenario: Upgrade cleans up a removed plugin
- **WHEN** a user upgrades the installer after a plugin was removed
- **THEN** that plugin's files installed by an earlier version are removed, and user-modified files are kept and reported

### Requirement: Unmaintained plugins are demoted

A `verified` plugin whose maintainers miss the response targets for 90 days, or that fails the eval gate for two consecutive releases of the plugin, SHALL be moved to `community`. A `community` plugin with no maintainer response for 180 days SHALL be deprecated. Each demotion SHALL be made in a PR that states the reason and is open for at least 14 days before merge.

#### Scenario: Demotion is announced
- **WHEN** a verified plugin is demoted
- **THEN** the PR states the missed target, and the next release notes list the tier change

### Requirement: Ownership can be handed over

A maintainer SHALL be able to step down by a PR that removes them from `catalog.yaml` and CODEOWNERS. A plugin left without maintainers SHALL be marked deprecated unless a new maintainer is added within 30 days.

#### Scenario: Last maintainer leaves
- **WHEN** a PR removes the only maintainer of a plugin
- **THEN** the PR also sets `status: deprecated`, or the ownership check fails
