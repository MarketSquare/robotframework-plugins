## 1. Copy the repository with history

- [x] 1.1 Fetch `manykarim/robotframework-agentskills` `main` into the new clone as branch `import/agentskills`. Merge it into a working branch with `--allow-unrelated-histories`, keeping the source `.gitignore` and the identical `LICENSE`. Verify that `git log --follow plugins/rf-agentskills/skills/rf-browser/SKILL.md` shows the original commits and that `8f24793` is an ancestor of the branch.
- [x] 1.2 Rebase or merge `plan/robotframework-plugins-programme` on top, so that `openspec/changes/launch-plugin-programme/` sits on the imported tree. Verify that `openspec validate launch-plugin-programme --strict` passes and that `openspec/specs/` matches the source's `main` except for the edited `agent-plugin-marketplace` Purpose.
- [ ] 1.3 Push the tags `v1.1.0`, `v1.2.0`, `v3.0.0` and `rf-agentskills-v0.3.0` to `rf-agentskills-v0.8.0` (release candidates included) to the new repository. Verify that `git rev-parse <tag>^{commit}` matches the old repository for every tag.
- [x] 1.4 Run the full test suite and the drift checks on the merged tree, with the installer `_assets/` built. Verify the same results as on the source `main` with the same environment (1,145 main, 566 eval; on 2026-11-08 both gave 1,140 passed, 1 failed, 4 skipped and 562 passed, 4 failed, all five failures from the local environment: Browser not initialised, and the session-start test's project venv).

## 2. Apply the rename map

- [x] 2.1 Rename the marketplace: `.claude-plugin/marketplace.json` name `robotframework-plugins`, owner Robot Framework Foundation / MarketSquare, plugin `homepage` and `repository` set to the new URL. Verify that `claude plugin validate plugins/rf-agentskills` and the manifest-consistency test pass.
- [x] 2.2 Rename the installer package to `robotframework-plugins`, the module `rf_agentskills` to `robotframework_plugins`, the CLI to `robotframework-plugins`, the project URLs and the release tag pattern to `robotframework-plugins-v*`. Set the version to the CalVer of the planned release month (for example `2026.12.0`). Verify that `uv build` in `installer/` produces `robotframework_plugins-<that version>` and that `uvx --from ./dist/<wheel> robotframework-plugins version` runs.
- [x] 2.3 Update the installer adapters and plugin mode to the new marketplace key and GitHub source, including the Codex commands. Verify with the updated `test_plugin_mode.py` scenarios from `installer-plugin-bootstrap`.
- [x] 2.4 Add migration of old `robotframework-agentskills` settings entries, keeping a `--ref` pin. Verify with a new test for the "Old marketplace entry migrated" scenario.
- [x] 2.5 Replace every remaining `manykarim/robotframework-agentskills` reference in tracked files outside the exempt paths (archived changes, changelogs, dated reports): README, `RELEASING.md`, `release.yml`, `plugin.json`, docs and tests. Verify that the "No stale repository references" scan in a new test returns only migration notes.

## 3. Plugin catalogue and layout

- [x] 3.1 Write `schemas/catalog.schema.json` and `plugins/rf-agentskills/catalog.yaml`: tier `verified`, status `active`, maintainers, libraries with version ranges, Robot Framework range and agents. Verify that schema validation passes, and fails on the two invalid fixtures from the `plugin-catalogue` scenarios.
- [x] 3.2 Write `scripts/build-catalog.py`. It generates the README catalogue table between markers and `docs/catalog.md`, and it writes the marketplace `tags` (tier, `deprecated`) and plugin list from the manifests. It has a `--check` mode. Verify that `--check` passes on the repository and fails after a summary edit without regeneration.
- [x] 3.3 Extend the installer build hook to bundle every active and deprecated plugin under `_assets/plugins/<name>/`, and record files per plugin in the install manifest. Verify that the wheel contains `_assets/plugins/rf-agentskills/` and that the existing installer tests pass.
- [x] 3.4 Add `install --plugins`, with the verified-plugins default, the unknown, removed and deprecated handling and a wizard step, plus `robotframework-plugins catalog [--json]`. Verify with tests for the "Default install", "Unknown plugin" and "Catalogue as JSON" scenarios, using a fixture catalogue with a community plugin.
- [x] 3.5 Move to one version per plugin: delete `VERSION`, remove `version` from the marketplace entry and `metadata.version` from `marketplace.json`, and change `scripts/bump-version.sh` to `<plugin> <major|minor|patch>`, writing `plugin.json` and the plugin's `SKILL.md` `metadata.version`. Update `test_marketplace_validation.py` and the skill validator. Verify that `claude plugin validate .` passes with no version warning and that the "Version stays in step" scenario passes.
- [x] 3.6 Remove root `skills/`, `scripts/sync-skills.sh` and the root-to-plugin checks in `scripts/check-drift.sh`, keeping the variant checks. Point `release.yml`'s tarballs, `scripts/build-skill-zips.py`, the installer build hook and tests at `plugins/<name>/skills/`. Verify that the release packaging dry run builds the same 9 skills and 3 tarballs as `v3.0.0`, and that `check-drift.sh` still catches a stale variant.
- [x] 3.7 Move plugin-specific tests to `plugins/rf-agentskills/tests/` and eval tasks and baselines to `plugins/rf-agentskills/evals/`, leaving the shared harness in `eval/` and repository checks in `tests/`. Add path-based selection to CI so a PR runs the shared tests and the changed plugins' tests. Verify the results from 1.4 are unchanged, and the "PR runs only the changed plugin's tests" scenario with a fixture second plugin.
- [x] 3.8 Add the catalogue checks for unique skill, subagent and hook-install names, for symlinks that leave the repository, and for the append-only `renames` map; generate `forceRemoveDeletedPlugins: true`. Verify with fixtures for "Duplicate skill name", "Link outside the repository" and "Renames history is append-only". (The security gate's expansion of a changed shared file moved to 5.4, which adds the gate.)
- [x] 3.9 Generate the version table (installer version plus each bundled plugin's name, version and tier) into the README, `docs/catalog.md` and `robotframework-plugins catalog [--json]`, and add it to installer release notes. Verify that `--check` fails after a plugin version bump without regeneration.

## 4. House content rules

Prerequisite: `split-rf-agentskills` is applied. Groups 4–10 work on its plugins, not on a single `rf-agentskills` plugin.


- [x] 4.1 Write `scripts/check_content_rules.py` covering every rule in `content-security-scanning`: Unicode tag and zero-width characters, HTML comments in `SKILL.md` and subagents, a missing or `*` subagent `tools` list, unrestricted shell in `allowed-tools`, piping downloads into a shell or interpreter in shipped code, unpinned MCP packages. Add tests using the spike canaries (C1–C6) as fixtures. Verify that canaries C1, C2, C3, C5 and C6 fail and the clean plugin passes. C4 (a hook script sending `process.env` with `fetch`) matches no house rule; the scanner gate catches it (5.4).
- [x] 4.2 Give `rf-test-architect` and `rf-migration-guide` explicit `tools` lists that match what their prompts do, and regenerate the Codex and OpenCode variants. Verify that `check_content_rules.py` passes, the variant drift check passes, and the subagent tests pass.

## 5. Security PR gate and deep scan

- [x] 5.1 Add `scripts/install-scanners.sh`, pinning Cisco skill-scanner 2.3.2, SkillSpector 2.13.4, cc-audit 3.23.37 (GitHub release binary with its checksum) and Gitleaks, each in its own virtualenv or directory. Verify that it installs on a clean Ubuntu runner and that every tool prints its pinned version.
- [x] 5.2 Add `scripts/compare-findings.py`. It normalises SARIF from each scanner to `(scanner, rule, file, fingerprint)`, compares it with `security/baselines/<plugin>.yaml`, fails on new HIGH or CRITICAL findings or expired entries, and writes a Markdown summary. Verify with unit tests for "Known false positive does not fail" and "Expired baseline entry".
- [ ] 5.3 Draft `security/baselines/rf-agentskills.yaml` from a clean scan. Review each entry with a reason, including the decisions on `curl | sh` for installing uv and on the lower-bound example pins, and set expiry dates. Verify that the gate passes on `main` with no unreviewed entries.
- [ ] 5.4 Add `.github/workflows/security-gate.yml` (`pull_request`, `contents: read`, no secrets). It runs the house rules, the scanners on changed plugins (a changed shared file counts as a change to every plugin that links to it; `scripts/select-plugin-tests.py` already computes this), cc-audit, Gitleaks and the comparison, and publishes SARIF as artifacts with a job summary. Add a nightly full scan. Verify on a test PR from a fork that the job runs without secrets, on a PR that adds the C4 hook canary that the gate fails, and with the "Shared hook change scans both plugins" fixture.
- [ ] 5.5 Add `.github/workflows/security-deep-scan.yml` (`pull_request_target` on the `security-deep-scan` label, and push to `main`). It checks out the PR head as data only, uses actions pinned to commit SHAs, runs the model-assisted SkillSpector and Cisco scans, comments the findings and sets a status check. Verify with a labelled test PR that the comment appears, and that an unlabelled PR does not run the job.
- [ ] 5.6 Restrict live `rf-skill-eval` workflows to `main`, maintainer branches and schedules. Verify that a fork PR does not trigger them, by reviewing the workflow triggers and with a dry run on a fork PR.
- [x] 5.7 Retest Gitleaks with a correctly shaped fake Anthropic key in a fixture. Verify that it is detected, or record which secret detector the gate uses instead.

## 6. Trust tiers and review

- [ ] 6.1 Create the Foundation reviewers team and the security reviewers team in MarketSquare (names to be confirmed), and add `.github/CODEOWNERS` mapping `plugins/<name>/` to maintainers and the security-relevant paths and `security/baselines/` to the security team. Verify that GitHub shows the owners on a test PR.
- [x] 6.2 Add `.github/workflows/required-reviews.yml` (plugin owners, Foundation reviewers for verified plugins, security reviewers for security-relevant paths) and the CODEOWNERS-to-`catalog.yaml` agreement check. Verify with tests on recorded PR payloads for "Hook change needs the security team", "Tier promotion needs a Foundation reviewer" and "CODEOWNERS drift".
- [x] 6.3 Add the tier evidence check: a verified plugin must have at least two maintainers, trigger sets, eval tasks and baselines. Verify with the "Verified without evals is refused" fixture.
- [ ] 6.4 Add the PR template with the review checklist, and enable branch protection on `main`: required checks are the security gate, required reviews, tests, catalogue and docs voice. Verify that a test PR shows the checklist and cannot merge while a required check fails.

## 7. Lifecycle

- [x] 7.1 Add lifecycle checks to `build-catalog.py --check`: a deprecated plugin needs `replacement` and `deprecated_since`; a plugin can be removed only after two content releases and 90 days; the marketplace must not list removed plugins; a plugin whose last maintainer leaves must be deprecated. Verify with fixtures for "Removal too early" and "Last maintainer leaves".
- [x] 7.2 Make installer upgrades remove the files of plugins that are no longer bundled, keeping and reporting user-modified files. Verify with a test for "Upgrade cleans up a removed plugin".

## 8. Adoption reporting

- [ ] 8.1 Add `.github/workflows/adoption-collect.yml`, which runs weekly and commits traffic JSON to the `adoption-data` branch. Verify after the first run that the branch has daily view and clone data; switch to a fine-grained token if `GITHUB_TOKEN` is refused.
- [x] 8.2 Add the feedback issue form with per-plugin labels, and `scripts/adoption-report.py` with a quarterly workflow that opens a PR with `docs/reports/adoption-<YYYY>-Q<n>.md`. Verify the report on fixture data, including a listed demotion candidate.
- [x] 8.3 Add a test that the installer makes no network calls during a file-mode install, by blocking sockets in the test process. Verify that the test passes.

## 9. Documentation in the Robot Framework Voice

- [ ] 9.1 Add `scripts/check-docs-voice.py` (banned phrases, at most one exclamation mark per document) to CI, with tests. Verify that the "Our mission is" fixture fails.
- [ ] 9.2 Write README.md: what it is, the catalogue (generated), install per agent with the new commands, the tiers and what they don't guarantee, no telemetry, and links. Verify that the docs voice check passes and a reviewer has checked the text against the voice guide.
- [ ] 9.3 Write CONTRIBUTING.md (adding a plugin, checks, review, writing rules), GOVERNANCE.md (tiers, review, maintainer targets, lifecycle) and SECURITY.md (private reporting, 7-day response, limits of the checks). Verify that the voice check passes and the GitHub Security tab shows the policy.
- [ ] 9.4 Add `templates/plugin/` with `catalog.yaml`, a README and one example skill, plus a CI job that copies it to `plugins/example/` in a scratch checkout and runs every PR check. Verify that the job passes.
- [ ] 9.5 Update `RELEASING.md` (plugin releases with `<plugin>--v*` tags, CalVer installer releases with `robotframework-plugins-v*` tags, the version table, trusted publishing), add the "Versions" section to `CONTRIBUTING.md`, and update the installer README and changelog, including the rename note. Verify that the voice check passes.

## 10. Release and switch-over

- [ ] 10.1 Configure the PyPI trusted publisher for `robotframework-plugins` and a protected `pypi` environment. Add the publish job to the release workflow, with the checks that the tag matches `pyproject.toml` and the release month, and change the plugin release trigger to `*--v*` with the tag-matches-`plugin.json` check. Verify on TestPyPI with a release-candidate tag.
- [ ] 10.2 Release the plugins from `split-rf-agentskills` (`rf-core`, `rf-web`, `rf-api`, `rf-mobile`, `rf-desktop` at 1.0.0 and the `rf-agentskills` 4.0.0 bundle) and the first CalVer release of `robotframework-plugins`. Do not release `rf-agentskills--v3.1.0`. Verify installs from the new marketplace on Claude Code, Copilot CLI and Codex, and `uvx robotframework-plugins install --agent claude-code --yes`, in isolated homes.
- [ ] 10.3 Build and publish the forwarding `rf-agentskills` 0.9.0, depending on `robotframework-plugins>=<the first CalVer release>`, from `legacy/rf-agentskills/`, then delete that folder. Verify that `uvx rf-agentskills install --agent claude-code --yes` prints the notice and installs.
- [ ] 10.4 Push the final README notice commit to `manykarim/robotframework-agentskills` and archive the repository. Verify that a marketplace add pinned to `v3.0.0` still installs, and that the README shows the notice.
- [ ] 10.5 Archive this change with its specs synced into `openspec/specs/`. Verify that `openspec validate --specs --strict` passes.
