# Releasing

Two kinds of release come out of this repository: a **plugin release**, which publishes one plugin's new version through the marketplace, and an **installer release**, which publishes `robotframework-plugins` to PyPI with a snapshot of the catalogue. They are independent: a plugin can release many times between installer releases.

## Versions

| What | Version scheme | Source of truth | Tag |
|---|---|---|---|
| Each plugin (`rf-core`, `rf-web`, …, the `rf-agentskills` bundle) | SemVer | `plugins/<plugin>/.claude-plugin/plugin.json` | `<plugin>--v<version>`, for example `rf-core--v1.0.0` |
| The installer `robotframework-plugins` | CalVer `YYYY.M.PATCH` | `installer/pyproject.toml` | `robotframework-plugins-v<version>`, for example `robotframework-plugins-v2026.12.0` |
| `rf-skill-eval` (internal) | SemVer | root `pyproject.toml` | none; never published |

The marketplace entries carry no version: Claude Code reads it from `plugin.json`. `CONTRIBUTING.md` ("Versions") explains which number to bump.

Older tags stay where they are: `v1.1.0` to `v3.0.0` are `rf-agentskills` content releases, and `rf-agentskills-v0.3.0` to `rf-agentskills-v0.8.0` are the installer under its old name. Old marketplace pins to them keep working.

## Plugin release

1. Bump the version and regenerate:
   ```bash
   scripts/bump-version.sh <plugin> <major|minor|patch>
   python scripts/build-catalog.py
   ```
   A change to a bundled plugin also changes the `rf-agentskills` bundle's copy; release the bundle too (`scripts/bump-version.sh rf-agentskills …`).
2. Add the release to `plugins/<plugin>/CHANGELOG.md`.
3. Merge the PR. Then tag the merge commit and push the tag:
   ```bash
   git tag <plugin>--v<version> && git push origin <plugin>--v<version>
   ```
4. `release.yml` checks that the tag matches the plugin's `plugin.json`, builds the plugin's archives, attaches them to a GitHub release and moves the `stable` and `latest` branches.

A pushed tag is the ref users pin a marketplace to: never move or delete one.

## Installer release

The installer version is the year and month of the release, then a patch number: the first release in December 2026 is `2026.12.0`, a fix in the same month `2026.12.1`.

1. Set `version` in `installer/pyproject.toml` and `__version__` in `installer/src/robotframework_plugins/__init__.py`, and add the release to `installer/CHANGELOG.md`.
2. Regenerate the version table in the README and `docs/catalog.md`: `python scripts/build-catalog.py`.
3. Merge the PR, then tag and push `robotframework-plugins-v<version>`.
4. `release.yml` checks that the tag matches `pyproject.toml` and the current month, builds the wheel and sdist, and creates the GitHub release. Its notes start with the table of bundled plugin versions (`python scripts/build-catalog.py --version-table`), then the changelog section.
5. The publish job uploads to PyPI with **trusted publishing**: PyPI accepts the upload from this repository's workflow, in the protected `pypi` environment, without a token. Nobody handles a PyPI token. A maintainer approves the `pypi` environment's deployment in the workflow run.
6. Check the published package:
   ```bash
   uvx --refresh robotframework-plugins@<version> version
   ```

A release candidate (`2026.12.0rc1`) goes through the same steps; it publishes to TestPyPI first, to check the flow.

## What the version table says

Each installer release bundles the active and deprecated plugins at their current versions. `build-catalog.py` writes that table into the README and `docs/catalog.md`, and `robotframework-plugins catalog --json` and `robotframework-plugins version` print it:

```console
$ robotframework-plugins version
robotframework-plugins 2026.12.0
bundled plugins: rf-agentskills 4.0.0, rf-api 1.0.0, rf-core 1.0.0, rf-desktop 1.0.0, rf-mobile 1.0.0, rf-web 1.0.0
```

So a user who reports a problem with "the installer from December" can be told exactly which plugin versions they have.

## Release notes

- A plugin release lists its changes from the plugin's changelog.
- An installer release starts with the version table, then lists the installer changes, and names every plugin that was added, deprecated, demoted or removed since the previous installer release ([GOVERNANCE.md](GOVERNANCE.md)).
