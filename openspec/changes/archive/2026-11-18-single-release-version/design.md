## Context

See proposal.md for why. The current state that shapes the approach:

- **Versions are written in four places.**
  - `plugins/<p>/.claude-plugin/plugin.json`: SemVer, `1.0.0`, bumped by `scripts/bump-version.sh <plugin> <part>`.
  - `metadata.version` in each `SKILL.md`, which `validate-skills.py` checks against `plugin.json`.
  - `installer/pyproject.toml` and `__init__.py`: CalVer `2026.11.0`, now yanked on PyPI together with `2026.11.0.dev1`.
  - Generated version tables in the README and `docs/catalog.md`.
- **`release.yml` has two job paths.**
  - `<plugin>--v*` runs `plugin-release` and `update-branches`.
  - `robotframework-plugins-v*` runs `installer-release` (with a month check) and `publish`.
  - A push of more than three tags at once starts no workflow at all (seen on 2026-11-18).
- **Existing tags.** `v1.1.0`, `v1.2.0` and `v3.0.0` are the old `rf-agentskills` content releases. Tags are never moved.
- **Plugin dependencies.** rf-web, rf-api, rf-mobile and rf-desktop declare `{"name": "rf-core", "version": "^1.0"}`, and so does `templates/plugin/`. Claude Code resolves a range against `<plugin>--v<version>` tags.
- **The bundle.** It is a catalogue entry with `bundle:` and no content. Code paths that handle it:
  - `build-catalog.py`: writes `bundles/` and checks it with `bundle_problems`;
  - `select-plugin-tests.py`, `security-scan.sh` and `check-drift.sh`;
  - `release.yml`: the tar step;
  - the installer: `_assets.is_bundle` and `expand_bundles`, and `_catalog.py`, which emits the `bundle` and `bundled` keys;
  - `adapters/_base.py`: maps the old `rf-agentskills@robotframework-agentskills` entry to the bundle.
- **The eval harness doesn't depend on the bundle.** It stages its own merged tree (`application/staging.py`).
- **What the agents require of versions.**
  - Claude Code: only `name` is required in `plugin.json`, and `version` is "a version string, not checked against semver". It is the cache key and the update signal per plugin, and bare-name dependencies resolve to whatever the marketplace provides ([dependencies](https://code.claude.com/docs/en/plugins/dependencies.md), [loading](https://code.claude.com/docs/en/plugins/loading.md)).
  - The Agent Plugins standard: `version` is optional, with Semantic Versioning recommended; updates and distribution are left to each client ([manifest](https://agent-plugins.org/plugin-authors/manifest)).
  - Copilot CLI and Codex ignore `dependencies` (measured 2026-11-08).

  Nothing requires plugins to have different versions.

## Goals / Non-Goals

**Goals:**
- A release is: one bump command, one changelog section, one PR, one tag, one workflow run, one approval.
- Nothing in the repository has to change per plugin when a release is made.
- After the change, `bundles/` and every bundle code path are gone. Only the public API keys stay, as constants.

**Non-Goals:**
- Changing what the plugins contain or how they are split.
- Renaming the installer's manifest folder (`rf-agentskills/installed.json`), which holds existing installs.
- Publishing the forwarder `rf-agentskills` 0.9.0. Only its dependency floor changes here; publishing it stays a separate, maintainer-approved step.
- Adopting the Agent Plugins root `plugin.json`. `agent-plugin-marketplace` forbids it, because Copilot CLI, Codex and Cursor would then treat hooks and subagents as unsupported.

## Decisions

### D1: One Semantic Version, starting at 5.0.0, with `installer/pyproject.toml` as its source

- **Why SemVer:** the Agent Plugins standard recommends it, Claude Code's dependency ranges use it, and users read a major number as "something breaks". CalVer only tells them the date.
- **Why 5.0.0:**
  - It continues the content line: `rf-agentskills` 1.x–3.0.0 as the old content releases, 4.0.0 the split, 5.0.0 one release for everything.
  - Every tag `v5.0.0` and later sorts above, and never equals, the old `v1.1.0`–`v3.0.0` tags.
  - The major bump marks the bundle's removal.
- **The source:** PyPI needs the version in `pyproject.toml`, so that file stays the one place where it's typed by hand. `build-catalog.py` writes:
  - every `plugin.json` `version`;
  - the installer's `__version__`;
  - the release line in the README and `docs/catalog.md`.

  `--check` fails on any copy that differs.
- **Release candidates:** the PEP 440 `5.1.0rc1` becomes the SemVer `5.1.0-rc.1` in `plugin.json`. The generator does this conversion, and the check compares the two forms after it.
- **`bump-version.sh <major|minor|patch>`:**
  - bumps the release version, and from a candidate finishes it (`5.1.0rc1` with `minor` gives `5.1.0`);
  - `--rc` starts or advances a candidate;
  - sets `pyproject.toml` and refreshes the installer's `uv.lock` entry;
  - runs the generator;
  - renames `## Unreleased` to `## <version> — <date>`.

*Alternatives:*
- CalVer (the first draft of this change): no judgement needed per release, but no breaking-change signal, unusual for plugins, and the installer's CalVer was only one day old.
- Restart at `1.1.0` with long tags (`robotframework-plugins-v1.1.0`): the plugins would continue from 1.0.0, but the tags are long and `v*` would stop meaning "a release".
- A root `VERSION` file: one more file, and `pyproject.toml` still has to carry the version.

### D2: Tag `v<version>`, with a version floor instead of a tag pattern

GitHub's tag filters can't express "greater than 3.0.0", so the workflow:
- triggers on `v[0-9]*`;
- fails its first step, before any build or publish, when the version is not greater than `3.0.0` or doesn't parse.

Re-pushing an existing tag starts no workflow, and the old tags are never moved, so the floor only guards against a mistaken new tag. `robotframework-plugins-v*` and `*--v*` are removed from the trigger. The month check goes, since the version no longer carries a date.

*Alternative:* the trigger patterns `v[5-9].*` and `v[1-9][0-9].*`. That keeps old tags out without a run, but it's easy to get wrong when the version reaches 100. The floor check is explicit and tested.

### D3: One `release.yml` flow

The jobs are:
- `ci`;
- `release`:
  - checks the tag against `pyproject.toml`, every `plugin.json` and the floor;
  - runs the drift check;
  - for each active plugin, builds `<plugin>-<version>.tar.gz` (without `tests/` and `evals/`) and `<plugin>-skills-<version>.tar.gz`;
  - builds the per-skill `rf-*.zip` files for all plugins;
  - builds the wheel and sdist with `build-packages.sh --check`;
  - writes the notes from `CHANGELOG.md`;
  - creates one GitHub release, a pre-release for a candidate;
- `publish`: PyPI, or TestPyPI for a candidate, in the protected environment;
- `update-branches`: moves `stable`; skipped for candidates, and run only after `publish` succeeds, so that `stable` never points at a release that isn't on PyPI.

Skill names are unique across the catalogue, which the catalogue check already enforces, so the per-skill zips of all plugins can share one `dist/`.

`update-branches` moves only `stable`. The `latest` branch is deleted after this change merges: since repo-cleanup D6 removed `update-latest.yml` it has held the same commit as `stable`, and few users have installed from this repository yet, so dropping it now costs least. Users pin `stable`, a release tag, or `main`.

### D4: Dependencies on `rf-core` by name only

`plugin.json` `dependencies` become `["rf-core"]`. Claude Code documents this form: "With a bare string, your plugin depends on whatever version that plugin's marketplace provides." Every plugin comes from the same marketplace commit at the same version, so a range adds nothing, and without `rf-core--v*` tags it can't be resolved against tags anyway. Copilot CLI and Codex ignore dependencies, and the README already tells their users to install `rf-core` explicitly.

The generator writes no version into dependencies, and the catalogue check refuses a dependency with a version range.

**Checked on 2026-11-18 (task 2.5):**
- Claude Code 2.1.322, from a git checkout of the branch added as a marketplace: `claude plugin install rf-web@robotframework-plugins` reported "+ 1 dependency: rf-core". Both plugins were enabled at `5.0.0`, and `claude plugin validate` passed for the marketplace and the plugins without warnings.
- VS Code Copilot 1.142, from the marketplace `MarketSquare/robotframework-plugins#stable` (release 5.0.0): installing `rf-web` from the Extensions view installed `rf-web` only. `~/.vscode/agent-plugins/installed.json` listed one plugin, and the agent saw only `rf-browser` and `rf-selenium`. VS Code doesn't install plugin dependencies in any form, so the D4 fallback (an exact version) wouldn't help. The name-only form stays, and the README tells VS Code users to install `rf-core` themselves, as for Copilot CLI and Codex.
- VS Code, project scope: a committed `.claude/settings.json` that named the marketplace and enabled `rf-web` neither added the marketplace nor offered the plugin. The README now says that each user adds the marketplace in their own settings. Task 2.4 confirms the install on Claude Code and VS Code. If VS Code needs a version, the fallback is an exact `"version": "=<release version>"` written by the generator. That still needs no tags, because a relative-path plugin falls back to the marketplace's copy.

### D5: Drop `metadata.version` from skills

`agentskills.io` doesn't require it, and keeping it in step would rewrite every `SKILL.md` on every release. `validate-skills.py` keeps checking for `author` and now fails on a `metadata.version`, so that one can't creep back in. The template skill follows.

### D6: One root `CHANGELOG.md`

```
# Changelog
## Unreleased
### Breaking / rf-core / rf-web / ... / Installer
## 5.0.0 — 2026-..-..
...
## History before one version
### Installer (robotframework-plugins, earlier rf-agentskills)
#### 2026.11.0 — 2026-11-18 (yanked)
...
### rf-core
#### 1.0.0 (2026-11-18)
...
```

Old entries move below, with their headings demoted one level so that the release-notes extraction (`## <version> `) never matches them. The separate files are deleted, and the plugin READMEs link to the root changelog.

### D7: Remove the bundle completely, keeping only the public keys

Everything in the bundle code paths goes, along with `bundles/` and `plugins/rf-agentskills/`. `_catalog.py` keeps emitting `bundle: false` and `bundled: []` (installer-python-api, ADDED requirement), and nothing else reads them.

The installer's old-entry migration (`enabled_marketplace_plugins`) maps `rf-agentskills@robotframework-agentskills` and `rf-agentskills@robotframework-plugins` to the five plugins. File mode already selects plugins by the skills an earlier install holds, so it needs no change.

### D8: One release version for community plugins too

GOVERNANCE.md says that a plugin's maintainers own its content and review, and that every plugin ships with the next release. A plugin that wants its own schedule would need a separate marketplace. No such plugin exists today.

## Risks / Trade-offs

- **[Risk] Users of the installer `2026.11.0` don't get `5.0.0` from `pip install -U` or `uv tool upgrade`, because it sorts lower.**
  - Both CalVer releases are yanked, so a fresh `uvx robotframework-plugins` and new installs resolve to `5.0.0`.
  - The release notes give the reinstall command. The installed base is a day old.
- **[Trade-off] A major bump for one plugin bumps them all.** A breaking change in rf-desktop makes rf-web `6.0.0` too, with nothing to act on. The changelog groups changes by plugin and says "no changes" where that applies.
- **[Trade-off] Every release bumps every plugin**, even an unchanged one. Agents re-download it, which costs nothing else.
- **[Risk] An agent doesn't install a name-only dependency.** Claude Code documents the form, and Copilot CLI and Codex ignore dependencies anyway. VS Code is checked in task 2.4, with the D4 fallback.
- **[Risk] Bundle users lose their plugin on the next Claude Code marketplace update** (`forceRemoveDeletedPlugins`).
  - Mitigation: a "Breaking" note at the top of `5.0.0`.
  - The installer migration enables the five plugins on the next `robotframework-plugins install`.
- **[Risk] Old pins `<plugin>--v1.0.0` stop receiving updates.** A pin to a tag never updates anyway, and the README tells pinned users to move to `v5.0.0` or later, or to `stable`.
- **[Risk] Someone tags `v3.0.1` or `v4.0.0` by mistake.** The floor check fails the run before anything is built or published (D2).

## Migration Plan

1. Land this change in one PR. CI proves that no `bundles/` and no per-plugin version remain, and that every version copy says `5.0.0`.
2. Release `5.0.0` with the new flow: merge, tag `v5.0.0`, approve `pypi`. The bump to `5.0.0` is part of this change, since it is a fixed starting point rather than a `bump-version.sh` step.
3. The `5.0.0` notes start with a "Breaking" section:
   - the bundle is gone, and what to install instead;
   - one version for everything, and the new tag form;
   - the reinstall line for `2026.11.0` users.
4. Rollback: revert the PR. No tag or branch is touched until `v5.0.0` is pushed, and existing tags are never moved. If `5.0.0` itself must be withdrawn, yank it on PyPI and fix forward with `5.0.1`.
