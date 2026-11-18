## Purpose

One version, one tag and one release for every plugin and the installer, so that a release is a single bump, a single tag push and a single workflow run.

## ADDED Requirements

### Requirement: One Semantic Version for every plugin and the installer

The repository SHALL have one release version, a Semantic Version `MAJOR.MINOR.PATCH`, shared by every plugin and the installer. The first release under it SHALL be `5.0.0`, and every later version SHALL be greater than `3.0.0`, so that no release tag can equal one of the old content tags `v1.1.0` to `v3.0.0`.

The release SHALL bump:
- **major** when it removes a plugin, changes a skill, subagent or hook in a way users must act on, or breaks the CLI or the Python API;
- **minor** when it adds a skill, a plugin or a feature;
- **patch** otherwise.

A release candidate SHALL be written `5.0.0rc1` (PEP 440) in the Python package, and `5.0.0-rc.1` (SemVer) in every `plugin.json`.

`installer/pyproject.toml` SHALL be the only place where the version is written by hand. Generated copies SHALL carry it:
- every plugin's `.claude-plugin/plugin.json`;
- the installer's `__version__`;
- the README and `docs/catalog.md`.

The catalogue check SHALL fail and name the file when a copy differs. A breaking change SHALL be listed under a "Breaking" heading in the changelog of the release that brings it, naming the plugin or tool it affects.

#### Scenario: A plugin's version is out of step
- **WHEN** `plugins/rf-web/.claude-plugin/plugin.json` says `5.0.0` and `installer/pyproject.toml` says `5.0.1`
- **THEN** `python scripts/build-catalog.py --check` fails and names `plugins/rf-web/.claude-plugin/plugin.json` and both versions

#### Scenario: One command bumps everything
- **WHEN** the release version is `5.0.0`, and a maintainer runs `scripts/bump-version.sh minor` and then `python scripts/build-catalog.py`
- **THEN** the installer and every plugin carry `5.1.0`, and the catalogue check passes

#### Scenario: Candidate spelling
- **WHEN** the version in `installer/pyproject.toml` is `5.1.0rc1` and the generator runs
- **THEN** every `plugin.json` says `5.1.0-rc.1`, and the catalogue check accepts the pair

### Requirement: One tag releases everything

A release SHALL be tagged `v<version>`, for example `v5.0.0`, on the commit that carries that version; a candidate uses the PEP 440 form, for example `v5.1.0rc1`. Pushing the tag SHALL run one release workflow that:
- fails before publishing anything when the tag's version differs from `installer/pyproject.toml` or from any `plugin.json`, or is not greater than `3.0.0`;
- builds every active plugin's archive, standalone skill archive and per-skill upload archives;
- builds the installer's wheel and sdist;
- creates one GitHub release with all of them attached;
- publishes the wheel and sdist through PyPI trusted publishing after a maintainer approves the protected `pypi` environment;
- moves `stable` to the tagged commit after the publish succeeds.

The tags from before this change (`v1.1.0` to `v3.0.0`, `rf-agentskills-v*`, `<plugin>--v*` and `robotframework-plugins-v*`) SHALL stay unchanged, and pushing one SHALL publish nothing.

#### Scenario: Release from one tag
- **WHEN** `v5.0.0` is pushed on a commit at version `5.0.0` and the `pypi` deployment is approved
- **THEN** one GitHub release `v5.0.0` holds an archive for each active plugin and the wheel and sdist, PyPI has `robotframework-plugins` `5.0.0`, and `stable` points at the tagged commit

#### Scenario: Tag and version disagree
- **WHEN** `v5.0.1` is pushed on a commit whose `installer/pyproject.toml` says `5.0.0`
- **THEN** the workflow fails before publishing anything and names both versions

#### Scenario: Old tags publish nothing
- **WHEN** a tag `v3.0.1`, `rf-core--v1.0.1` or `robotframework-plugins-v2026.11.1` is pushed
- **THEN** no release is created and nothing is published

### Requirement: Releases have one moving branch

`stable` SHALL be the only branch a release moves, and the repository SHALL have no `latest` branch: it held the same commit as `stable` and was removed in 5.0.0. Users pin `stable` for the latest release, a release tag for a fixed one, and `main` for unreleased changes.

#### Scenario: No latest after a release
- **WHEN** release `v5.0.0` has run
- **THEN** `stable` points at the tagged commit, the repository has no `latest` branch, and no workflow creates or moves one

### Requirement: Release candidates do not move the release branches

A release candidate tag such as `v5.1.0rc1` SHALL go through the same workflow, but it SHALL publish to TestPyPI, mark the GitHub release as a pre-release, and leave `stable` where it is.

#### Scenario: Candidate release
- **WHEN** `v5.1.0rc1` is pushed
- **THEN** the wheel goes to TestPyPI, the GitHub release is a pre-release, and `stable` still points at the previous release

### Requirement: One changelog for the release

The repository SHALL keep one `CHANGELOG.md` at its root:
- an `## Unreleased` section at the top;
- one section per release, headed `## <version> — <date>`;
- within a section, changes grouped by plugin and installer, with breaking changes listed first.

Plugins and the installer SHALL NOT keep their own changelogs. Entries from before this change SHALL stay in the root changelog under their original headings. The release notes SHALL be that release's section.

#### Scenario: Release notes from the changelog
- **WHEN** `v5.0.0` is released
- **THEN** the GitHub release body holds the `5.0.0` section of `CHANGELOG.md`, and no `plugins/*/CHANGELOG.md` or `installer/CHANGELOG.md` exists
