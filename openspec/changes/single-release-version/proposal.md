## Why

The first real release on 2026-11-18 needed six plugin tags, one installer tag, seven changelogs and two PRs. Pushing more than three tags at once started no workflow at all. Most of that work comes from two choices that no longer pay off:

- Each plugin has its own version, and the installer has a third kind (CalVer).
- The `rf-agentskills` bundle ships a second, generated copy of every plugin.

Few users adopted the bundle. It doubles every skill change (`bundles/`, 145 files), needs its own release, and must grow with every new plugin. The project is still being set up, so this is the time to simplify, before the plugin count grows.

## What Changes

- **BREAKING** Remove the `rf-agentskills` bundle at once, with no deprecation period, since the project is still being set up:
  - `plugins/rf-agentskills/`, `bundles/rf-agentskills/` and its marketplace entry;
  - the `bundle` field of `catalog.yaml`;
  - the bundle code in the catalogue generator, the security scan, the plugin test selection, the drift check and the release workflow.

  Claude Code uninstalls the plugin for users who enabled it; the release notes tell them to install `rf-core` and the technology plugins.
- **BREAKING** Give all plugins and the installer **one version**: a Semantic Version, released together.
  - The next release is **`5.0.0`**. It continues the content line, where `v1.1.0` to `v3.0.0` were the `rf-agentskills` content releases and 4.0.0 the split, and its major number marks the bundle's removal.
  - The plugins move from `1.0.0`, and the installer from CalVer `2026.11.0`, to `5.0.0`.
  - `installer/pyproject.toml` is the one source. `scripts/build-catalog.py` writes it into every `plugin.json`, and its `--check` fails when one differs.
  - A release candidate is `5.0.0rc1` on PyPI and `5.0.0-rc.1` in `plugin.json`, the SemVer form that the Agent Plugins standard recommends.
- **BREAKING** The installer leaves calendar versions. PyPI `2026.11.0` and `2026.11.0.dev1` are already yanked, so resolvers pick `5.0.0`. Existing installs of `2026.11.0` must reinstall, because `5.0.0` sorts lower; the release notes say so.
- **BREAKING** Use one release tag, `v<version>`, for example `v5.0.0`.
  - It replaces `<plugin>--v<version>` and `robotframework-plugins-v<version>`.
  - The release workflow refuses any version not above `3.0.0`, so the old content tags `v1.1.0` to `v3.0.0` stay inert.
  - One tag push runs one release that builds every plugin's archives, the wheel and the sdist, creates one GitHub release, publishes to PyPI after approval, and moves `stable`.
  - Existing tags stay where they are.
- **BREAKING** Remove the `latest` branch. Since repo-cleanup removed `update-latest.yml` it held the same commit as `stable`. Releases move only `stable`, and `fetch()` names a release tag or `main` when `stable` is missing.
- Plugin dependencies on `rf-core` name the plugin without a version range. Claude Code documents this form ("depends on whatever version that plugin's marketplace provides"), every plugin is released at one version from one commit, and no `rf-core--v*` tags exist to resolve a range against.
- Drop `metadata.version` from `SKILL.md` frontmatter and the rule that it must match `plugin.json`. Otherwise every release would rewrite every skill.
- One `CHANGELOG.md` at the repository root replaces the six plugin changelogs and `installer/CHANGELOG.md`.
  - It is grouped by plugin within each release.
  - Earlier entries are kept below the new ones, under their old headings.
- The per-plugin version table in the README, `docs/catalog.md` and the release notes becomes one line naming the release.
- Simplify `scripts/bump-version.sh` (`<major|minor|patch>` for the whole release), `RELEASING.md`, `CONTRIBUTING.md` ("Versions"), `GOVERNANCE.md` and the README install sections accordingly.
- The installer's upgrade from the old `rf-agentskills@robotframework-agentskills` marketplace entry enables `rf-core`, `rf-web`, `rf-api`, `rf-mobile` and `rf-desktop` instead of the bundle, so nothing a user had disappears.
- `bundle.catalog()` keeps the `bundle` and `bundled` keys, always `false` and `[]`, so `CATALOG_FORMAT` stays `1` for tools such as rf-mcp.
- The unpublished forwarder `rf-agentskills` 0.9.0 depends on `robotframework-plugins>=5.0.0` instead of `>=2026.11.0`.

## Capabilities

### New Capabilities
- `release-train`: one version and one tag for every plugin and the installer. It covers the version's format and single source, the generated copies, the release workflow, release candidates, and the one changelog.

### Modified Capabilities
- `agent-plugin-marketplace`:
  - the marketplace no longer lists the bundle;
  - dependencies name `rf-core` without a range;
  - releases are tagged `v<version>` instead of per plugin;
  - pinning documentation uses the release tag.
- `plugin-split`: the bundle requirement is removed.
- `plugin-catalogue`:
  - the per-plugin version table becomes the release version;
  - shared-file copies no longer mention the bundle.
- `installer-onboarding`: the installer's calendar-version requirement is removed, because `release-train` defines the shared version, and the publish scenario uses the release tag.
- `installer-plugin-bootstrap`: the old marketplace entry migrates to the five plugins.
- `skill-metadata-conformance`: `metadata.version` is no longer required or checked against `plugin.json`.
- `skill-catalog`: the MCP-server prohibition applies to every plugin, not "the bundle".
- `programme-documentation`:
  - `CONTRIBUTING.md` explains that contributors never bump versions;
  - `RELEASING.md` describes the one release.
- `installer-python-api`:
  - the missing-`stable` message no longer says that the first plugin release creates `stable`;
  - an added requirement keeps the `bundle` and `bundled` keys constant.
- `repository-migration`: the forwarder depends on the first release under the shared version instead of the first calendar-version release.

## Impact

- **Removed:**
  - `plugins/rf-agentskills/` and `bundles/`;
  - the bundle paths in `scripts/build-catalog.py`, `scripts/select-plugin-tests.py`, `scripts/security-scan.sh`, `scripts/check-drift.sh` and `.github/workflows/release.yml`;
  - the `bundle` field in `schemas/catalog.schema.json`;
  - `expand_bundles` and `is_bundle` in the installer;
  - the bundle fixtures in about ten test files;
  - the month check in the release workflow.
- **Changed:**
  - `.github/workflows/release.yml`: one tag pattern, a version floor and one job flow;
  - `scripts/bump-version.sh`: takes `major`, `minor` or `patch` for the whole release;
  - `scripts/validate-skills.py`: no version rule;
  - every `plugin.json`: a generated version and name-only dependencies;
  - 49 `SKILL.md` files: `metadata.version` removed;
  - `installer/src/robotframework_plugins/adapters/_base.py`: the old-entry migration;
  - the root `CHANGELOG.md` and the plugin changelogs;
  - `legacy/rf-agentskills/pyproject.toml`: the dependency floor;
  - `README.md`, `RELEASING.md`, `CONTRIBUTING.md`, `GOVERNANCE.md`, `docs/catalog.md`, `AGENTS.md` and `openspec/config.yaml`.
- **Users:**
  - Bundle users must install the separate plugins; skill prefixes change from `rf-agentskills:` to the plugin's own.
  - A marketplace pinned to `<plugin>--v1.0.0` keeps working, but receives no updates until it is re-pinned to `v5.0.0` or later, or to `stable`.
  - Users of the installer `2026.11.0` reinstall (`uv tool install --force robotframework-plugins` or `pip install --force-reinstall robotframework-plugins==5.0.0`).
- **Kept:**
  - the forwarder `legacy/rf-agentskills/` (only its floor changes);
  - all existing tags;
  - the installer's `rf-agentskills/installed.json` manifest location;
  - the eval harness's merged staging tree, which never depended on the bundle.
- **Sequencing:** the open `add-rf-bdd-skill` change should land after this one, so that it needs no bundle or version edits.
