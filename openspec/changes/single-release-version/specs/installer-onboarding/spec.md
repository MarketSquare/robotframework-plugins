## MODIFIED Requirements

### Requirement: Zero-install entry point via PyPI

The `robotframework-plugins` package SHALL be published to PyPI so it can be run without a prior install, mirroring `npx`-style usage. Releases SHALL be published from the release workflow with PyPI trusted publishing (GitHub OIDC) from a protected `pypi` environment, without a long-lived PyPI token. The final `rf-agentskills` release SHALL forward to it, as `repository-migration` defines.

#### Scenario: uvx / pipx run works
- **WHEN** a user runs `uvx robotframework-plugins install` (or `pipx run robotframework-plugins install`)
- **THEN** the published package resolves from PyPI and the installer runs

#### Scenario: Release publishes without a stored token
- **WHEN** a release tag `v<version>` is pushed and a maintainer approves the `pypi` environment
- **THEN** the wheel and sdist for `<version>` are published to PyPI through trusted publishing, and the repository has no PyPI token secret

## REMOVED Requirements

### Requirement: Installer versions are calendar versions

**Reason**: The installer no longer has a version of its own. It shares the release version, a Semantic Version, with every plugin, and its tag is the release tag. PyPI `2026.11.0` and `2026.11.0.dev1` are yanked, so resolvers pick `5.0.0` and later.

**Migration**: `release-train` defines the version, the `v<version>` tag and the release workflow's checks. Users of `2026.11.0` reinstall, because `5.0.0` sorts lower: `uv tool install --force robotframework-plugins`. Existing `robotframework-plugins-v*` tags stay unchanged.
