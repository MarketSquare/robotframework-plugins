## 1. Close `launch-plugin-programme` (D8)

- [x] 1.1 For launch task 1.3, compare `git rev-parse <tag>^{commit}` in the new repository with `manykarim/robotframework-agentskills` for every listed tag; verify they all match, then tick 1.3 with the result. Done: all 14 tags match (`git ls-remote` of both repositories, 2026-11-16).
- [x] 1.2 In `openspec/changes/launch-plugin-programme/tasks.md`:
  - tick 5.4, 5.6, 6.4, 9.2, 9.3, 9.4 and 10.1, each with its evidence from design D8;
  - mark 6.1 "superseded by `lean-governance`";
  - mark 5.5, 8.1 and 10.2–10.4 "carried over to `lean-governance`". Done.

  Verify that the only unticked tasks left in the change are 6.1 (superseded), the carried-over 5.5, 8.1 and 10.2–10.4 (each with its note), and 10.5.
- [x] 1.3 Archive `launch-plugin-programme` with its specs synced (`/opsx:archive`). Verify that `openspec validate --specs --strict` passes and that `openspec validate lean-governance` no longer reports "target spec does not exist". Done: archived as `2026-11-16-launch-plugin-programme` (+37, ~11, -6 requirements); `openspec validate --specs --strict` passes 31/31. The `plugin-trust-tiers` delta here now removes "Verified tier entry criteria" and adds "Verified tier is decided by evidence", because a MODIFIED block can't drop the old "Tier promotion needs a Foundation reviewer" scenario.

## 2. Checks and scripts (D4, D5)

- [x] 2.1 Reduce `scripts/check-governance.py` to the tier evidence: drop the maintainer count, Foundation membership, `tier_grace`, `--today`, `--team-members` and the CODEOWNERS agreement. Update `tests/test_governance.py`: keep "Verified without evals is refused", and add "One maintainer is enough" and "Same tree, later date" (run with the clock patched to 2027-02-01). Verify that `pytest tests/test_governance.py` passes and `python scripts/check-governance.py` prints no warning. Done: 6 tests pass; the check prints `governance: tier evidence OK`.
- [x] 2.2 Add `--warn-days` (default 30) and `--fail-on-warn` to `scripts/compare-findings.py`, and pass `--fail-on-warn` from `security-gate.yml` only on `schedule` and `workflow_dispatch` runs. Add tests in `tests/test_compare_findings.py` for "Expiry is flagged ahead": a 20-day entry gives a warning and exit 0, and exit 1 with `--fail-on-warn`. Verify that `pytest tests/test_compare_findings.py` passes. Done: `security-scan.sh --fail-on-warn` passes the flag through; tests pass. Earliest real expiry is 2027-11-08, so the nightly scan doesn't fail today.
- [x] 2.3 Delete `scripts/required-reviews.py`, the required-review tests in `tests/test_governance.py`, `tests/fixtures/required-reviews/` and `.github/governance.yaml`. Remove `.github/governance.yaml` and `scripts/required-reviews.py` from every list that names them (CODEOWNERS, `check_content_rules.py` or `security-scan.sh` path lists, if any). Verify that `grep -rn "required-reviews\|governance.yaml" --exclude-dir=openspec .` only finds the workflow files deleted in 3.1. Done: the grep only finds `tests/test_governance.py`, which asserts the file is gone.
- [x] 2.4 Replace `.github/CODEOWNERS` with a default owner line for the maintainers (D1), and update `scripts/check-template.sh` and `templates/plugin/` if they mention CODEOWNERS lines per plugin. Verify that `bash scripts/check-template.sh` passes. Done: `* @manykarim`; `check-template.sh` no longer adds a CODEOWNERS line and passes.

## 3. Workflows, template and docs (D3, D7)

- [x] 3.1 Delete `.github/workflows/required-reviews.yml` and `.github/workflows/review-relay.yml`, and update the ci.yml comment at the `check-governance.py` step. Verify that `actionlint` (or `gh workflow list` after merge) shows neither workflow. Done: workflows deleted; the ci.yml step is now "Tier evidence". actionlint isn't installed locally (the YAML parses); `gh workflow list` is checked after merge.
- [x] 3.2 Rewrite `.github/pull_request_template.md` as in D7: "What this changes", "Checked by CI" with no checkboxes, and "For the reviewer". Leave a marked spot for the AI disclosure line from `ai-contributor-docs`. Verify that the template names only checks that exist in `ci.yml` and `security-gate.yml`. Done.
- [x] 3.3 Rewrite GOVERNANCE.md:
  - Tiers: evidence only.
  - Review: the two rulesets, one approval for external PRs, maintainers merge on green.
  - Keep the commitments and the lifecycle as they are. Done: the voice check passes and the grep finds nothing.

  Then update:
  - the CONTRIBUTING.md "Review" section and step 4 of "Adding a plugin", which drops the CODEOWNERS line and mentions the plugin's maintainers in the PR instead;
  - the README "Trust tiers" section;
  - the SECURITY.md sentence about security reviewers.

  Verify that `python scripts/check-docs-voice.py` passes, and that `grep -rn "Foundation reviewer\|security reviewer\|required-reviews" README.md CONTRIBUTING.md GOVERNANCE.md SECURITY.md` finds nothing.
- [x] 3.4 Run `pytest tests --ignore=tests/eval`, `python scripts/build-catalog.py --check` and `bash scripts/check-template.sh`; verify that all of them pass. Done: `pytest tests --ignore=tests/eval` 804 passed, 40 skipped (libraries not installed locally); `build-catalog.py --check` and `check-template.sh` pass.

## 4. GitHub settings (maintainer step; ask before each change)

- [x] 4.1 Save the current ruleset with `gh api repos/MarketSquare/robotframework-plugins/rulesets/26891587 > ruleset-main-before.json` (scratch, not committed). No team (D1, confirmed 2026-11-16). Verify that the JSON file is saved. Done: saved to the scratchpad as `ruleset-main-before.json` (ruleset `main`, active).
- [x] 4.2 With the maintainer's approval, create the two rulesets from D2 and delete ruleset 26891587:
  - `main-checks`: today's required checks minus `required-reviews`, no deletion, no force push, no bypass;
  - `main-review`: 1 approval, code owner review, dismiss stale approvals, bypass for the Maintain and Admin roles in `pull_request` mode. Done 2026-11-16: `main-checks` (id 27388961, 11 required checks, no bypass) and `main-review` (id 27388964, 1 code-owner approval, stale approvals dismissed, bypass for Maintain and Admin in `pull_request` mode) are active; ruleset 26891587 is deleted; `required-reviews` is not a required check.

  Verify with `gh api .../rulesets` that both rulesets are active and that `required-reviews` is no longer a required check.
- [x] 4.3 Approved on 2026-11-16 (D6); confirm the timing with the maintainer, then enable repository auto-merge, secret scanning, push protection and Dependabot security updates. Verify that `gh api repos/MarketSquare/robotframework-plugins --jq '.allow_auto_merge, .security_and_analysis'` shows all of them enabled. Done 2026-11-16: auto-merge, secret scanning, push protection, vulnerability alerts and Dependabot security updates are enabled (0 secret-scanning alerts).

## 5. Dry run and carried-over launch tasks

- [x] 5.1 Merge the PR with tasks 2–3 through the maintainer bypass. Then verify:
  - a maintainer test PR (a docs typo) merges with no approval once its checks pass;
  - a test PR from a fork, or from an account without write access, shows "1 approving review required";
  - a test PR with a failing check can't be merged, even with the bypass. Done 2026-11-16: #25 merged through the maintainer bypass with no approval; the fork PRs #11–#18 show "review required"; the bypass merge of the dry-run PR #26 (a docs voice failure) was refused with "9 of 11 required status checks have not succeeded", and #26 was closed unmerged. `gh workflow list` no longer shows the two review workflows (task 3.1).

  Close both test PRs without merging.
- [x] 5.2 (Launch 5.5) Find out why the `security-deep-scan.yml` push runs on `main` fail, fix it, and verify with a labelled test PR that the comment appears and that an unlabelled PR doesn't run the job. In progress: the push runs fail because the repository has no `SECURITY_SCAN_ANTHROPIC_API_KEY` secret, so `security-scan.sh --deep` stops and the next `cat` of the missing summary fails the job. The workflow now reports "not run" without a key (warning, an `error` status and a comment on a labelled PR) and handles a missing summary. The maintainer chose OpenRouter with a dedicated key (`SECURITY_SCAN_OPENROUTER_API_KEY`, added 2026-11-16): `security-scan.sh` gets `SECURITY_SCAN_PROVIDER` (openrouter by default, model `z-ai/glm-5.3-flash`; anthropic stays available), and the workflow passes the new key. A local run with stub scanners shows both scanners get the OpenRouter settings. Still open: after merge, the push run on `main` must pass, and a labelled test PR that plants the C4 hook (`fetch(..., process.env)`) must be flagged with the comment; if GLM 5.3 Flash misses it, switch `vars.SECURITY_SCAN_MODEL` to a stronger OpenRouter model. Update 2026-11-17: the C4 test PR #28 was flagged by the static gate (Cisco `DATA_EXFIL_ENV_DUMP`) and by the GLM pass (three HIGH findings on the planted hook), so GLM 5.3 Flash stays. The first push run on `main` (43915965731) failed on six model findings that #28 didn't reproduce, and the label trigger hit GitHub's `pull_request_target` brownout; design D9 moves the scan to `workflow_dispatch` by PR number and makes model findings report-only on `main`. Still open after that PR merges: the push run on `main` passes, and a dispatched scan of a test PR posts the comment. Done 2026-11-17: #29 merged (`e030691`) and the `security-deep-scan` label was deleted. The push run on `main` (44036421187) passed, with a warning for new model findings in rf-desktop. On test PR #30, a dispatch with an outdated `sha` stopped before the model pass, and a dispatch with the current head posted the comment and set the `security-deep-scan` status (red on a GLM false positive in the bundle copy of an rf-requests example, which rf-api's own scan passed). #30 was closed unmerged.
- [ ] 5.3 (Launch 8.1) After the next weekly `adoption-collect.yml` run, verify that the `adoption-data` branch has daily view and clone data; switch to a fine-grained token if `GITHUB_TOKEN` is refused. In progress: a manual run on 2026-11-16 got HTTP 403 from the traffic API with `GITHUB_TOKEN`. The maintainer adds an `ADOPTION_TOKEN` secret (fine-grained, this repository, Administration: read); then a run is verified. Update 2026-11-17: the secret is added; the token waits for approval by a MarketSquare owner. Until then the run fails with a message naming the pending approval. Once approved, start `adoption-collect.yml` by hand and check the `adoption-data` branch.
- [ ] 5.4 (Launch 10.2) Release the plugins and `robotframework-plugins`. Verify installs from the marketplace on Claude Code, Copilot CLI and Codex, and `uvx robotframework-plugins install --agent claude-code --yes`, in isolated homes. Update 2026-11-18: superseded in part by single-release-version. The plugins were released at 1.0.0 and `rf-agentskills` at 4.0.0 on 2026-11-18, then everything again as 5.0.0 (tag `v5.0.0`), which removed the bundle; the CalVer `2026.11.0` is yanked. Verified so far: Claude Code installs `rf-web` with `rf-core` from `stable`, both at 5.0.0, and a plain `uvx robotframework-plugins` resolves 5.0.0. Still open: the Copilot CLI and Codex installs and the `install --agent claude-code --yes` run, in isolated homes.
- [ ] 5.5 (Launch 10.3) Build and publish the forwarding `rf-agentskills` 0.9.0 from `legacy/rf-agentskills/`, then delete that folder. Verify that `uvx rf-agentskills install --agent claude-code --yes` prints the notice and installs.
- [ ] 5.6 (Launch 10.4) Push the final README notice to `manykarim/robotframework-agentskills` and archive it. Verify that a marketplace add pinned to `v3.0.0` still installs and that the README shows the notice.

## 6. Initial check

- [ ] 6.1 After tasks 1–5, review each confirmed decision against what happened. Did any PR get stuck? Did the maintainer bypass work? Did the scanners or push protection block real work? Did the 30-day warning fire? Write down the findings. If one shows a problem or a risk, propose the changed decision to the maintainer and update `design.md` before archiving. Verify that the findings are recorded in this change.
