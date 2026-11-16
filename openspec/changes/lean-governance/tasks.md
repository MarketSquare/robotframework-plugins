## 1. Close `launch-plugin-programme` (D8)

- [ ] 1.1 For launch task 1.3, compare `git rev-parse <tag>^{commit}` in the new repository with `manykarim/robotframework-agentskills` for every listed tag; verify they all match, then tick 1.3 with the result.
- [ ] 1.2 In `openspec/changes/launch-plugin-programme/tasks.md`:
  - tick 5.4, 5.6, 6.4, 9.2, 9.3, 9.4 and 10.1, each with its evidence from design D8;
  - mark 6.1 "superseded by `lean-governance`";
  - mark 5.5, 8.1 and 10.2–10.4 "carried over to `lean-governance`".

  Verify that `openspec list` shows no unticked task in the change other than 10.5.
- [ ] 1.3 Archive `launch-plugin-programme` with its specs synced (`/opsx:archive`). Verify that `openspec validate --specs --strict` passes and that `openspec validate lean-governance` no longer reports "target spec does not exist".

## 2. Checks and scripts (D4, D5)

- [ ] 2.1 Reduce `scripts/check-governance.py` to the tier evidence: drop the maintainer count, Foundation membership, `tier_grace`, `--today`, `--team-members` and the CODEOWNERS agreement. Update `tests/test_governance.py`: keep "Verified without evals is refused", and add "One maintainer is enough" and "Same tree, later date" (run with the clock patched to 2027-02-01). Verify that `pytest tests/test_governance.py` passes and `python scripts/check-governance.py` prints no warning.
- [ ] 2.2 Add `--warn-days` (default 30) and `--fail-on-warn` to `scripts/compare-findings.py`, and pass `--fail-on-warn` from `security-gate.yml` only on `schedule` and `workflow_dispatch` runs. Add tests in `tests/test_compare_findings.py` for "Expiry is flagged ahead": a 20-day entry gives a warning and exit 0, and exit 1 with `--fail-on-warn`. Verify that `pytest tests/test_compare_findings.py` passes.
- [ ] 2.3 Delete `scripts/required-reviews.py`, the required-review tests in `tests/test_governance.py`, `tests/fixtures/required-reviews/` and `.github/governance.yaml`. Remove `.github/governance.yaml` and `scripts/required-reviews.py` from every list that names them (CODEOWNERS, `check_content_rules.py` or `security-scan.sh` path lists, if any). Verify that `grep -rn "required-reviews\|governance.yaml" --exclude-dir=openspec .` only finds the workflow files deleted in 3.1.
- [ ] 2.4 Replace `.github/CODEOWNERS` with a default owner line for the maintainers (D1), and update `scripts/check-template.sh` and `templates/plugin/` if they mention CODEOWNERS lines per plugin. Verify that `bash scripts/check-template.sh` passes.

## 3. Workflows, template and docs (D3, D7)

- [ ] 3.1 Delete `.github/workflows/required-reviews.yml` and `.github/workflows/review-relay.yml`, and update the ci.yml comment at the `check-governance.py` step. Verify that `actionlint` (or `gh workflow list` after merge) shows neither workflow.
- [ ] 3.2 Rewrite `.github/pull_request_template.md` as in D7: "What this changes", "Checked by CI" with no checkboxes, and "For the reviewer". Leave a marked spot for the AI disclosure line from `ai-contributor-docs`. Verify that the template names only checks that exist in `ci.yml` and `security-gate.yml`.
- [ ] 3.3 Rewrite GOVERNANCE.md:
  - Tiers: evidence only.
  - Review: the two rulesets, one approval for external PRs, maintainers merge on green.
  - Keep the commitments and the lifecycle as they are.

  Then update:
  - the CONTRIBUTING.md "Review" section and step 4 of "Adding a plugin", which drops the CODEOWNERS line and mentions the plugin's maintainers in the PR instead;
  - the README "Trust tiers" section;
  - the SECURITY.md sentence about security reviewers.

  Verify that `python scripts/check-docs-voice.py` passes, and that `grep -rn "Foundation reviewer\|security reviewer\|required-reviews" README.md CONTRIBUTING.md GOVERNANCE.md SECURITY.md` finds nothing.
- [ ] 3.4 Run `pytest tests --ignore=tests/eval`, `python scripts/build-catalog.py --check` and `bash scripts/check-template.sh`; verify that all of them pass.

## 4. GitHub settings (maintainer step; ask before each change)

- [ ] 4.1 Save the current ruleset with `gh api repos/MarketSquare/robotframework-plugins/rulesets/26891587 > ruleset-main-before.json` (scratch, not committed). No team (D1, confirmed 2026-11-16). Verify that the JSON file is saved.
- [ ] 4.2 With the maintainer's approval, create the two rulesets from D2 and delete ruleset 26891587:
  - `main-checks`: today's required checks minus `required-reviews`, no deletion, no force push, no bypass;
  - `main-review`: 1 approval, code owner review, dismiss stale approvals, bypass for the Maintain and Admin roles in `pull_request` mode.

  Verify with `gh api .../rulesets` that both rulesets are active and that `required-reviews` is no longer a required check.
- [ ] 4.3 Approved on 2026-11-16 (D6); confirm the timing with the maintainer, then enable repository auto-merge, secret scanning, push protection and Dependabot security updates. Verify that `gh api repos/MarketSquare/robotframework-plugins --jq '.allow_auto_merge, .security_and_analysis'` shows all of them enabled.

## 5. Dry run and carried-over launch tasks

- [ ] 5.1 Merge the PR with tasks 2–3 through the maintainer bypass. Then verify:
  - a maintainer test PR (a docs typo) merges with no approval once its checks pass;
  - a test PR from a fork, or from an account without write access, shows "1 approving review required";
  - a test PR with a failing check can't be merged, even with the bypass.

  Close both test PRs without merging.
- [ ] 5.2 (Launch 5.5) Find out why the `security-deep-scan.yml` push runs on `main` fail, fix it, and verify with a labelled test PR that the comment appears and that an unlabelled PR doesn't run the job.
- [ ] 5.3 (Launch 8.1) After the next weekly `adoption-collect.yml` run, verify that the `adoption-data` branch has daily view and clone data; switch to a fine-grained token if `GITHUB_TOKEN` is refused.
- [ ] 5.4 (Launch 10.2) Release `rf-core`, `rf-web`, `rf-api`, `rf-mobile` and `rf-desktop` at 1.0.0, the `rf-agentskills` 4.0.0 bundle and the first CalVer release of `robotframework-plugins`. Verify installs from the marketplace on Claude Code, Copilot CLI and Codex, and `uvx robotframework-plugins install --agent claude-code --yes`, in isolated homes.
- [ ] 5.5 (Launch 10.3) Build and publish the forwarding `rf-agentskills` 0.9.0 from `legacy/rf-agentskills/`, then delete that folder. Verify that `uvx rf-agentskills install --agent claude-code --yes` prints the notice and installs.
- [ ] 5.6 (Launch 10.4) Push the final README notice to `manykarim/robotframework-agentskills` and archive it. Verify that a marketplace add pinned to `v3.0.0` still installs and that the README shows the notice.

## 6. Initial check

- [ ] 6.1 After tasks 1–5, review each confirmed decision against what happened. Did any PR get stuck? Did the maintainer bypass work? Did the scanners or push protection block real work? Did the 30-day warning fire? Write down the findings. If one shows a problem or a risk, propose the changed decision to the maintainer and update `design.md` before archiving. Verify that the findings are recorded in this change.
