## Context

See proposal.md (Why). The state on 2026-11-16 that shapes the approach:

- **Ruleset `main` (id 26891587, active)** has these rules:
  - deletion and non-fast-forward;
  - a `pull_request` rule with `required_approving_review_count: 0` and `require_code_owner_review: false`;
  - 12 required checks, including `required-reviews` and `Security gate result`.

  Its only bypass actor is the Admin repository role in `pull_request` mode. No classic branch protection.
- **Six people have the Admin role**: emanlove, Hi-Fi, aaltat, Noordsestern, Simakvokka and manykarim. Ten more have Read. The teams `robotframework-plugins-reviewers` and `-security` return 404, and `REVIEW_TEAMS_TOKEN` isn't set, so `required-reviews.yml` reads empty team lists.
- **Repository settings:**
  - `allow_auto_merge` is false;
  - secret scanning, push protection and Dependabot security updates are disabled;
  - there is no `.github/dependabot.yml`.
- **The `required-reviews` machinery** is `required-reviews.yml` (133 lines), `review-relay.yml`, `scripts/required-reviews.py` (155 lines), `.github/governance.yaml` (teams, 26 security paths, `tier_grace` until 2027-01-31) and the test cases and fixtures in `tests/test_governance.py`.
- **`check-governance.py`** has two parts:
  - CODEOWNERS ↔ `catalog.yaml` agreement;
  - verified evidence, with grace by date.

  It runs in `ci.yml` (Lint job) and in `scripts/check-template.sh`.
- **External contributors:** #11–#18 come from one external contributor. Two of them add community plugins (`rf-mind`, `rf-maestro`).

## Goals / Non-Goals

**Goals:**
- GitHub enforces review natively; no workflow computes approvals.
- A maintainer PR needs no second human. An external PR needs exactly one.
- Nothing in governance fails because the calendar moved.

**Non-Goals:**
- Changing the security gate's scanners, rules or baselines themselves.
- Changing the lifecycle rules (deprecation, removal, demotion) or the maintainer response targets in GOVERNANCE.md.
- Dependabot version updates and auto-merging bot PRs. There are no bot PRs today; that can be added when there are (see Open Questions).
- Creating any GitHub team. The maintainers are the repository roles.

## Decisions

### D1 Maintainers are a repository role, not a team

The maintainers are the people with the Maintain or Admin role. Rulesets can name roles as bypass actors directly, and CODEOWNERS needs owners with write access anyway. That leaves no team to create, no token to read members, and no list to keep in sync.

`CODEOWNERS` becomes a single default line, `* @manykarim`, plus any other maintainer who wants review requests. It names people because CODEOWNERS can't name a role.

*Alternative: a `robotframework-plugins-maintainers` team.* It's tidier once there are several active maintainers, but it needs an org owner to create it. Kept as an option for the maintainer step (task 4.1); CODEOWNERS can switch to it in one line.

### D2 Two rulesets, so checks can't be bypassed while review can

A ruleset's bypass list applies to all of its rules. One ruleset therefore can't let maintainers skip the approval while still forcing them through the checks. The split:

| Ruleset | Rules | Bypass |
|---|---|---|
| `main-checks` | required status checks (today's list minus `required-reviews`), no deletion, no force push | none |
| `main-review` | pull request: 1 approval, code owner review, dismiss stale approvals | Maintain and Admin roles, `pull_request` mode |

In `pull_request` mode, a maintainer can merge their own green PR with "bypass rules" on the PR page, but can't push to `main` directly. Turning on repository auto-merge lets a maintainer arm "merge when ready", so nobody has to come back to press the button.

*Alternative: keep `required_approving_review_count: 0` and rely on the security gate alone.* That would let an external PR merge with no human looking at it. One approval for outsiders is the minimum that still stops a hostile plugin from landing on green checks.

### D3 Remove `required-reviews`, don't slim it

Once D2 is in place, the check has nothing left to decide: the plugin-owner, Foundation and security groups all go away. The workflows, the script, `governance.yaml` and the fixtures are deleted.

Order matters. `required-reviews` must leave the required checks (task 4.2) before the workflow is deleted, otherwise every open PR waits forever for a status nobody sets.

### D4 Tier evidence only; no grace, no dates

`check-governance.py` keeps the tier evidence: trigger sets, narrow tasks and baselines for every skill, and a bundle being verified only if all its members are. It drops:
- the maintainer count;
- Foundation membership;
- `tier_grace`, `--today` and `--team-members`;
- the CODEOWNERS ↔ `catalog.yaml` agreement, which D1 makes meaningless because plugin maintainers no longer appear in CODEOWNERS.

The security gate and the keyword check, which `verified` now names, are already required checks on every PR, so the tier check doesn't run them again. It only has to show that they exist for the plugin, which they do for every plugin.

`catalog.yaml` keeps `maintainers` (at least one; the catalogue check already refuses an active plugin with nobody listed), because users and the lifecycle rules need a named person.

### D5 Baseline expiry stays, but warns ahead

Expiry is the one date-driven failure that is deliberate: an accepted finding gets looked at again within 12 months. To keep it from surprising an unrelated PR, `compare-findings.py` gets a `--warn-days 30` window:
- in PR runs, an entry inside the window is a warning in the summary;
- with `--fail-on-warn`, which the scheduled `security-gate.yml` run on `main` passes, it is a failure.

A maintainer therefore sees the nightly failure up to 30 days before any PR would.

### D6 Turn on GitHub's free protections

For a public repository, secret scanning, push protection and Dependabot security updates cost nothing and need no review. Push protection catches a leaked key before it reaches a PR, earlier than the PR gate's Gitleaks step, which stays. Dependabot security updates only open PRs when an advisory hits a locked dependency. Those PRs go through the same checks and a maintainer arms auto-merge.

### D7 The PR template asks only what checks can't answer

The template has three parts:
- **What this changes** (free text);
- **Checked by CI**: a plain list with no checkboxes. It covers the security gate, skill validation and links, `.robot` dry runs, keyword check, catalogue and docs voice;
- **For the reviewer**: "Anything the checks can't see, such as a behaviour change, a new tool permission, or a judgement call?"

Change B adds an AI disclosure line under the free text. Both changes edit only their own sections, so whichever is applied second rebases cleanly.

### D8 Reconcile `launch-plugin-programme` here

The launch change can't be archived with 15 open tasks, and several of them are about the review model this change replaces. Evidence gathered on 2026-11-16:

| Launch task | State | Evidence | Action |
|---|---|---|---|
| 1.3 tags | done | `v1.1.0`, `v1.2.0`, `v3.0.0`, `rf-agentskills-v0.3.0`…`v0.8.0` (incl. rc) exist in the new repo | tick, after the commit comparison in task 1.1 |
| 5.4 security gate | done | `security-gate.yml` runs on `pull_request` (forks included, #11–#18), nightly cron; `Security gate result` is a required check | tick |
| 5.5 deep scan | built, not verified | workflow exists; the last 3 push runs on `main` failed | carry over as task 5.1 here |
| 5.6 live evals not on forks | done | `skill-evaluation.yml` treats a fork PR as having no credentials (comment at line 175; "Evaluation not run (no credentials)" job) | tick |
| 6.1 two teams | superseded | replaced by D1/D2 | mark superseded |
| 6.4 template and protection | done, then changed here | PR template exists; ruleset `main` requires the checks | tick, noting that D2 and D7 replace both |
| 8.1 adoption data | built, not verified | `adoption-collect.yml` exists; no run and no `adoption-data` branch yet | carry over |
| 9.2, 9.3, 9.4 docs and template | done | README, CONTRIBUTING, GOVERNANCE and SECURITY exist and pass the voice check; `Template plugin passes the PR checks` is a required check | tick |
| 10.1 trusted publishing | done | `pypi` and `testpypi` environments; `robotframework-plugins` 2026.11.0.dev1 on PyPI from `release.yml` | tick |
| 10.2–10.4 releases and switch-over | open | no `<plugin>--v*` tags; `rf-agentskills` on PyPI is 0.8.0; the old repo isn't archived | carry over |
| 10.5 archive | — | done by task 1.3 here | tick when archived |

The carried-over tasks aren't about governance. They move here only so the launch change can close; their wording doesn't change.

### D9 The deep scan starts by PR number, and only reports on main

Two things showed up once the deep scan had a key (task 5.2):
- **The label trigger stops working.** GitHub blocks `pull_request_target` in public repositories from 2026-12-02 unless an admin allows it, and `actions/checkout` then also needs an explicit opt-in to check out a fork's head. The labelled run on 2026-11-16 already hit the brownout (`startup_failure`).
- **Model findings can't gate `main`.** The first push run on `main` (43915965731) failed on six new model findings, one of them a CRITICAL false positive. The same content scanned in #28 didn't produce them. The fingerprint includes the model's wording, so these findings can't be baselined either.

The workflow therefore runs on `workflow_dispatch` with a `pr` input, plus an optional `sha` for the reviewed head. Only people with write access can start a workflow, which is the same approval the label was. The PR head is fetched as `refs/pull/<n>/head` with plain git, without credentials, and checked against the head commit the API reports. On `main`, findings become a warning and a summary; only a scan that stops before writing its summary fails the run. The static scanners still gate every PR (`Security gate result`) and the nightly `security-gate.yml` run.

Rejected: asking an admin to allow `pull_request_target` and adding the checkout opt-in. That keeps the event that runs with secrets next to fork code, and it depends on an organisation setting.

## Risks / Trade-offs

- **[A maintainer merges a harmful change of their own on green checks]** → The checks (house rules, scanners, Gitleaks, push protection) are the same for everyone. The bypass is logged on the PR. With one active maintainer, a second human approval was never actually happening anyway.
- **[An external PR gets one approval from a maintainer who skims it]** → The security gate must pass too. The template's "for the reviewer" question points at what to read by hand, and a maintainer can start the deep scan for the PR (D9).
- **[Plugin maintainers from outside lose their say over changes to their plugin]** → They never had an enforceable say, because GitHub doesn't count approvals from people without write access. CONTRIBUTING asks authors to mention a plugin's maintainers in the PR, and maintainers can be given the Write role later.
- **[Removing the `required-reviews` status before the rulesets exist]** → task 4 applies the rulesets first, and task 3 deletes the workflow after that.
- **[Dependabot PRs add noise]** → Security updates only, no version updates.

## Migration Plan

1. Archive `launch-plugin-programme` after reconciling it (task 1), so the deltas in this change have main specs to apply to.
2. Prepare the code and doc changes (tasks 2–3) on a branch and open the PR. `required-reviews` runs base-branch code, so it keeps waiting for the security group on this PR (it touches workflows); that is expected.
3. Maintainer step (task 4), before step 2's PR merges:
   - create `main-checks` and `main-review`;
   - delete the old `main` ruleset;
   - turn on auto-merge, secret scanning, push protection and Dependabot security updates.
4. Merge the PR. The workflows are gone and the rulesets enforce review.
5. Dry run (task 5): a maintainer PR merges with no approval; a test PR from a fork can't merge until one approval; a failing check blocks both.

**Rollback:** restore the old ruleset from its JSON (saved in task 4.1) and revert the merge commit.

## Confirmed decisions (maintainer, 2026-11-16)

Each decision stands for now. After implementation, the check in task 6.1 confirms it. If that check, or anything found along the way, shows a problem or a risk, the decision can change again. In that case, update this design before going on.

- **D1:** maintainers are the Maintain and Admin repository roles, with `* @manykarim` in CODEOWNERS. No team.
- **D5:** baseline expiry is the one check that may fail because of a date. The nightly scan warns 30 days ahead.
- **D6:** turn on secret scanning, push protection, Dependabot security updates and repository auto-merge. Auto-merge for bot PRs stays open (see below).

## Open Questions

- Should Dependabot version updates, and auto-merge for their patch bumps, be added later? That would be its own small change once version drift becomes a chore; it doesn't affect this design.
