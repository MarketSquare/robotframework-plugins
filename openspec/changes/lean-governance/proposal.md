## Why

The review model from `launch-plugin-programme` was designed for a Foundation programme with several reviewers. In practice the repository has one active maintainer and no review teams, and the model already gets in the way:
- The Foundation reviewers and security reviewers teams don't exist, or can't be read: the team API returns 404, and the `REVIEW_TEAMS_TOKEN` secret the check needs isn't set. A PR that needs either group can never pass `required-reviews`, so every maintainer PR that touches a plugin is merged with the admin bypass.
- External contributors are already here: eight open PRs (#11–#18), two of which add community plugins. Under the current rules a new plugin's only "owner" is its author, whose approval doesn't count, so those PRs can't pass without a bypass either.
- `check-governance.py` fails every PR on 2027-01-31, when the `tier_grace` entry for "second maintainer, Foundation maintainer" runs out.

The maintainer's direction: review and approval should be as lean as needed, and most checks should be automated, with little to no human intervention.

## What Changes

- **One maintainers group.** The repository's people with the Maintain or Admin role are the maintainers. The Foundation reviewers team, the security reviewers team and the `foundation`/`security` groups go away.
- **Native enforcement.** Two GitHub rulesets on `main` replace the custom review check:
  - **checks**: the required status checks, no bypass for anyone;
  - **review**: one approval from a code owner, which maintainers may bypass when they merge through a PR.

  So a maintainer's own PR merges once all automated checks pass, and an external PR needs one maintainer approval. Repository auto-merge is enabled, so a PR can be set to merge itself when it goes green.
- **BREAKING (contributors):** `.github/workflows/required-reviews.yml`, `.github/workflows/review-relay.yml`, `scripts/required-reviews.py`, its tests and fixtures, and the `required-reviews` status are removed. `.github/governance.yaml` is removed; `CODEOWNERS` gets a default owner (the maintainers) and drops the per-plugin team lines.
- **Security by automation, not a second team.** Security-relevant paths are guarded by the security gate, which is already a required check: house content rules, scanners, Gitleaks and the reviewed baseline. GitHub secret scanning, push protection and Dependabot security updates, all disabled today, are turned on. The `security-deep-scan` label stays.
- **Tiers from evidence, not head counts.** `verified` requires the automated evidence only: trigger sets, eval tasks, baselines on the current models, a passing eval gate, a passing security gate and keyword check. The "two maintainers, one from the Foundation team" rule and `tier_grace` are dropped. No check fails because a date has passed, except the security baseline's expiry, which the nightly scan now flags 30 days ahead.
- **A short PR template.** The six human checkboxes become a list of what the checks cover plus two questions the checks can't answer. Change B (`ai-contributor-docs`) adds the AI disclosure line to the same template.
- **Docs.** GOVERNANCE.md, the CONTRIBUTING "Review" section, the README "Trust tiers" section and SECURITY.md describe the lean model.
- **Reconcile `launch-plugin-programme`** so it can be archived. Tick the tasks that are done, with evidence, mark 6.1 (create two teams) as superseded, and carry the release and switch-over tasks that remain (8.1, 10.2–10.4) into this change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `plugin-trust-tiers`:
  - verified criteria lose the maintainer counts and team membership;
  - review becomes one maintainer approval for external PRs, with maintainers merging their own PRs on green checks;
  - the PR template lists the automated checks;
  - tier results don't depend on the date.
- `content-security-scanning`:
  - security-relevant content no longer needs a security team approval;
  - baseline changes need no security team;
  - the nightly scan fails 30 days before a baseline entry expires;
  - repository secret scanning and push protection are on.

Both capabilities are added by the unarchived change `launch-plugin-programme`; this change modifies its requirements. `launch-plugin-programme` is archived first (task 1), so the deltas here apply to the synced main specs.

## Impact

- **Workflows and scripts:**
  - removed: `required-reviews.yml`, `review-relay.yml`, `scripts/required-reviews.py`;
  - changed: `scripts/check-governance.py` (tier evidence only; no `--today`, no `tier_grace`), `scripts/compare-findings.py` (30-day warning; nightly mode fails on it), `security-gate.yml` (nightly mode flag), `scripts/check-template.sh`.
- **Config:**
  - removed: `.github/governance.yaml`;
  - changed: `.github/CODEOWNERS`, `.github/pull_request_template.md`.
- **Tests:** `tests/test_governance.py` (the required-review cases are removed, the tier cases kept), `tests/fixtures/required-reviews/` (removed), and `tests/test_compare_findings.py`.
- **GitHub settings (maintainer step, asked before applying):**
  - ruleset `main` (id 26891587) is split into "checks" and "review";
  - `required-reviews` is removed from the required checks;
  - auto-merge, secret scanning, push protection and Dependabot security updates are enabled;
  - optionally a `robotframework-plugins-maintainers` team.
- **Docs:** GOVERNANCE.md, CONTRIBUTING.md, README.md ("Trust tiers"), SECURITY.md, RELEASING.md (nothing about review there today; checked).
- **Open PRs #11–#18:** after the switch they need one maintainer approval and green checks, with no `required-reviews` status.
- **Related changes:**
  - `ai-contributor-docs` edits the same PR template and CONTRIBUTING.md. Apply this change first, or rebase B's template edit on it.
  - `repo-cleanup` doesn't touch these files.
