## 1. Remove the bundle (D7)

- [x] 1.1 Delete `plugins/rf-agentskills/` and `bundles/`, and drop the bundle from the generated marketplace.
  - In `scripts/build-catalog.py`, remove the bundle generation, `BUNDLES_REL`, the bundle source path and `bundle_problems`.
  - Refuse a `bundle` key in `catalog.yaml`.
  - Remove `bundle` from `schemas/catalog.schema.json`.

  Verify: `python scripts/build-catalog.py --check` passes, `.claude-plugin/marketplace.json` lists exactly rf-core, rf-api, rf-desktop, rf-mobile and rf-web with `rf-core` first, and a fixture `catalog.yaml` with `bundle:` fails the check.
- [x] 1.2 Remove the bundle handling from `scripts/select-plugin-tests.py`, `scripts/security-scan.sh` (bundle members and baselines) and `scripts/check-drift.sh` (the `bundles/*` paths). Verify: `bash scripts/check-drift.sh` passes, and `tests/test_plugin_test_selection.py` passes with the bundle cases removed.
- [x] 1.3 Remove `is_bundle` and `expand_bundles` from the installer, and their callers in `_assets.py`, `cli.py` and `transforms.py`. Keep `bundle: false` and `bundled: []` in every `_catalog.py` entry. Verify: a test asserts both keys on every `bundle.catalog()` entry and `CATALOG_FORMAT == 1`, and `tests/installer` passes.
- [x] 1.4 Remove the bundle fixtures and cases from the tests: `test_catalog.py`, `test_marketplace_validation.py`, `test_skill_validation.py`, `test_skill_descriptions.py`, `test_compare_findings.py`, `test_drift_detection.py`, `test_governance.py`, and the installer tests `conftest.py`, `test_split_upgrade.py`, `test_plugin_selection.py` and `test_removed_plugin_upgrade.py`. Verify: `uv run pytest` passes, and `git grep -n "bundles/" -- tests scripts installer/src src .github` finds nothing.

## 2. One Semantic Version (D1, D4, D5)

- [x] 2.1 Let `scripts/build-catalog.py` write the version from `installer/pyproject.toml` into every `plugin.json`, the installer's `__version__`, and the release line in `README.md` and `docs/catalog.md`.
  - Convert a PEP 440 candidate (`5.1.0rc1`) to SemVer (`5.1.0-rc.1`) for `plugin.json`.
  - Let `--check` name each differing file and both versions.
  - Let `--check` refuse a version that is not greater than `3.0.0`.

  Verify: tests on a scratch tree show:
  - a hand-edited `plugin.json` version fails the check, naming the file;
  - `5.1.0rc1` produces `5.1.0-rc.1` in every `plugin.json`;
  - `3.0.0` is refused.
- [x] 2.2 Set the release version to `5.0.0`: `installer/pyproject.toml`, `uv.lock`, and the generated copies. Verify: `build-catalog.py --check` passes, and every `plugin.json` and `robotframework_plugins.__version__` say `5.0.0`.
- [x] 2.3 Rewrite `scripts/bump-version.sh` to take `major`, `minor` or `patch`, plus `--rc` to start or advance a candidate.
  - It sets `installer/pyproject.toml`, refreshes the installer's entry in `uv.lock`, runs the generator, and renames `## Unreleased` to `## <version> — <date>`.
  - The old `<plugin> <part>` form exits non-zero with usage.

  Verify: a scratch-tree test covers `5.0.0` with `minor` (gives `5.1.0`), `--rc minor` (gives `5.1.0rc1` and `5.1.0-rc.1`) and `patch` from `5.1.0rc1` (gives `5.1.0`), and shows that no `SKILL.md` changed.
- [x] 2.4 Remove `metadata.version` from every `SKILL.md`, including `templates/plugin/`. In `scripts/validate-skills.py`, drop the version-mismatch rule and add a rule that fails on `metadata.version`. Verify: `python scripts/validate-skills.py --channel all` passes, and a fixture skill with `metadata.version` fails naming the skill.
- [ ] 2.5 Change the `rf-core` dependencies of rf-web, rf-api, rf-mobile, rf-desktop and `templates/plugin/` to `["rf-core"]` (D4), and let the catalogue check refuse a dependency version range.
  - Then install `rf-web` from a git checkout of the branch, served as a marketplace, in Claude Code and in VS Code Copilot.
  - If VS Code needs a version, switch to the generator-written exact version (D4 fallback).

  Verify: `claude plugin validate .` passes without a version-mismatch warning, and `claude plugin install rf-web@robotframework-plugins` also installs `rf-core`. Record each agent's result in design.md D4.

  Status: the code change and the Claude Code check are done (design D4). The VS Code Copilot check is still open.

## 3. Release workflow (D2, D3)

- [x] 3.1 Rewrite `.github/workflows/release.yml`.
  - Trigger on `v[0-9]*` only.
  - The first step of `release` fails before any build when the version is not greater than `3.0.0`, doesn't parse, or differs from `pyproject.toml` or any `plugin.json`.
  - Then it builds every active plugin's archives, all per-skill zips, the wheel and the sdist, and creates one GitHub release from the `CHANGELOG.md` section, a pre-release for `rcN`.
  - Then `publish` (PyPI, or TestPyPI for `rcN`), then `update-branches`, which is skipped for candidates and runs only after `publish`.
  - Remove the month check.

  Verify: the workflow tests in `tests/` assert:
  - the trigger pattern;
  - the floor and version checks come before any build step;
  - the job order `ci → release → publish → update-branches`;
  - the candidate conditions;
  - that no job references `bundles/`, `--v` or a month.
- [x] 3.2 Check the release-notes step against the new changelog. Verify: a test runs the notes extraction on a sample `CHANGELOG.md` and gets exactly the `5.0.0` section, never a demoted history heading.

- [x] 3.3 Let `scripts/adoption-report.py` (`--evals-from-git`) read each plugin's eval history from the release tags `v<version>` above `3.0.0` as well as the older `<plugin>--v*` tags, so the report keeps getting new releases. Found during implementation. Verify: a test in `tests/test_adoption_report.py` tags a scratch repository with `v3.0.0`, `rf-core--v1.0.0`, `v5.0.0` and `v5.1.0rc1`, and gets exactly `1.0.0` and `5.0.0`.

## 4. One changelog (D6)

- [x] 4.1 Create the root `CHANGELOG.md` with `## Unreleased` and a "History before one version" part.
  - Move `installer/CHANGELOG.md` and each `plugins/*/CHANGELOG.md` there, with their headings demoted one level, and mark `2026.11.0` and `2026.11.0.dev1` as yanked.
  - Delete the old files.
  - Point the plugin READMEs, `installer/README.md` and the installer's package metadata (`project.urls` changelog, if set) at it.

  Verify: no `plugins/*/CHANGELOG.md` or `installer/CHANGELOG.md` exists, `git grep -n "CHANGELOG.md"` finds only links to the root file, and `python scripts/check-docs-voice.py` passes.
- [x] 4.2 Write the `5.0.0` entry under `## Unreleased`, with "Breaking" first:
  - the bundle is removed, and what to install instead;
  - one version for every plugin and the installer, and why `5.0.0`;
  - `v<version>` tags;
  - the reinstall line for `2026.11.0` users;
  - name-only dependencies;
  - no skill `metadata.version`.

  Verify: the entry names `rf-core`, the four technology plugins, `v5.0.0` and the reinstall command.

  Done as `## 5.0.0 — 2026-11-18`, not under `## Unreleased`. This change sets `5.0.0` directly instead of through `bump-version.sh`, and the release notes need the version's own section. If the release is tagged on a later day, correct the date in the release PR.

## 5. Installer and forwarder

- [x] 5.1 In `adapters/_base.py`, map `rf-agentskills@robotframework-agentskills` and `rf-agentskills@robotframework-plugins` to rf-core, rf-web, rf-api, rf-mobile and rf-desktop when no `--plugins` is given, keeping the `--ref` pin. Verify: the "Old marketplace entry migrated" and "Bundle entry replaced" scenarios pass as tests in `tests/installer/test_plugin_mode.py`.
- [x] 5.2 Change the missing-`stable` hint in `_snapshot.py` to name a release tag `v<version>` and `main`, without "the first plugin release". Verify: the test in `tests/installer/test_bundle_fetch.py` checks the new message.
- [x] 5.3 Make `robotframework-plugins version` show the one release version once, followed by the plugin names. Keep `version` per entry in `catalog --json`. Verify: `tests/installer/test_cli.py` checks both outputs.
- [x] 5.4 Set the forwarder's dependency in `legacy/rf-agentskills/pyproject.toml` to `robotframework-plugins>=5.0.0`, and update its description if it names a CalVer version. Verify: `uv build legacy/rf-agentskills` succeeds, and the built metadata's `Requires-Dist` says `robotframework-plugins>=5.0.0`. Publishing it stays a separate step that the maintainer approves.

## 6. Documentation and project context

- [x] 6.1 Update `README.md`.
  - Remove the bundle row, the "bundle or separate plugins" section, the prefix warning and the "everything at once" lines.
  - Pin examples use `v5.0.0` and `stable`, with the note about old tags.
  - The catalogue table has one release line.

  Verify: `git grep -n "rf-agentskills" README.md` finds only the history note, and `check-docs-voice.py` passes.
- [x] 6.2 Rewrite `RELEASING.md` for the one release:
  - which part to bump;
  - `bump-version.sh`, then changelog, then PR, then tag `v<version>`, then approve `pypi`, then check with `uvx`;
  - candidates;
  - "never move a tag";
  - the floor;
  - the manual Claude eval note.

  Rewrite the `CONTRIBUTING.md` "Versions" section: never bump; add a changelog entry under Unreleased. Verify: both scenarios of `programme-documentation` hold by reading, and `check-docs-voice.py` passes.
- [x] 6.3 Update `GOVERNANCE.md` (D8: every plugin ships with the release), `AGENTS.md` (generated files and commands without `bundles/`), the `openspec/config.yaml` context (no bundle), `docs/catalog.md`, and the bundle and CalVer mentions in `docs/ci/architecture/adr/ADR-005-ci-integration.md`, `installer/README.md` and the issue template. Verify: `git grep -n -e "bundles/" -e "rf-agentskills bundle" -e "CalVer" -- ':!openspec/changes/archive' ':!docs/archive' ':!legacy' ':!CHANGELOG.md'` finds nothing, and `python scripts/check-governance.py` passes.

## 7. Verify and ship

- [x] 7.1 Run every check in AGENTS.md: `build-catalog.py --check`, `check-governance.py`, `validate-skills.py --channel all`, `check-plugin-references.py`, `check-skill-keywords.py --require-all`, `check-robotcode-first.py`, `check-docs-voice.py`, `openspec validate --all --strict` and `uv run pytest`. Verify: all pass locally.

  Done 2026-11-18: every check passes. The tests pass: 920 shared tests, 559 plugin tests and 634 eval-harness tests. Deselected: the eval cases that need Browser's Node dependencies (`rfbrowser init`), SeleniumLibrary or robocop, which this local venv lacks and CI installs.
- [x] 7.2 Open the PR with an "AI assistance" section, wait for every check to be green, and merge. Verify: the PR is merged with no failed check, and its description lists the user-facing breaking changes.
- [ ] 7.3 Release `5.0.0` after asking the maintainer: push the single tag `v5.0.0` on the merge commit, and the maintainer approves `pypi`. Verify:
  - one GitHub release `v5.0.0` holds five plugin archives and the wheel and sdist;
  - `uvx --refresh robotframework-plugins@5.0.0 version` prints `5.0.0`, and a plain `uvx --refresh robotframework-plugins version` resolves to `5.0.0`, not the yanked `2026.11.0`;
  - `stable` points at the tag;
  - in Claude Code, an updated `rf-core` reports `5.0.0`.

  Status 2026-11-18: `v5.0.0` was pushed on `dfdd180`. The first run of the new workflow exposed two gaps:
  - The `pypi` and `testpypi` environments allowed only `robotframework-plugins-v*` tags. They now allow `v*`.
  - `build-packages.sh --clean` deleted the plugin archives. The workflow now builds the packages first and attaches only archives. For 5.0.0, the 19 plugin and skill archives were built from the tag and uploaded to the release by hand.

  Still to do: approve the `pypi` deployment, then check PyPI and `stable`.
- [x] 7.4 Delete the `latest` branch on GitHub after this change merges. Verify: `git ls-remote --heads origin latest` prints nothing.
