## MODIFIED Requirements

### Requirement: Zero-install entry point via PyPI

The `robotframework-plugins` package SHALL be published to PyPI so it can be run without a prior install, mirroring `npx`-style usage. Releases SHALL be published from the release workflow with PyPI trusted publishing (GitHub OIDC) from a protected `pypi` environment, without a long-lived PyPI token. The final `rf-agentskills` release SHALL forward to it, as `repository-migration` defines.

#### Scenario: uvx / pipx run works
- **WHEN** a user runs `uvx robotframework-plugins install` (or `pipx run robotframework-plugins install`)
- **THEN** the published package resolves from PyPI and the installer runs

#### Scenario: Release publishes without a stored token
- **WHEN** an installer release tag `robotframework-plugins-v<version>` is pushed and a maintainer approves the `pypi` environment
- **THEN** the wheel and sdist for `<version>` are published to PyPI through trusted publishing, and the repository has no PyPI token secret

## ADDED Requirements

### Requirement: Installer versions are calendar versions

`robotframework-plugins` SHALL use versions of the form `YYYY.M.PATCH` without zero padding: the year and month of the release, and a patch number that starts at 0 each month. The release tag SHALL be `robotframework-plugins-v<version>`, and the release workflow SHALL fail when the tag's year and month don't match the release date or the version in `installer/pyproject.toml`. A breaking change to the CLI SHALL be announced in the changelog of the release before it lands.

#### Scenario: Second release in a month
- **WHEN** `2026.12.0` was released and a fix is released later in December 2026
- **THEN** its version is `2026.12.1`

#### Scenario: Wrong month fails
- **WHEN** a tag `robotframework-plugins-v2026.11.0` is pushed in December 2026
- **THEN** the release workflow fails before publishing and states the expected `2026.12.<n>`
