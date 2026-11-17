## MODIFIED Requirements

### Requirement: Review follows a published checklist

Every PR SHALL use a PR template that lists the automated checks the PR must pass and asks the author for what the checks can't show: what the change is for, and anything a reviewer should look at by hand. The template SHALL NOT ask authors or reviewers to tick items that a required check already verifies.

#### Scenario: New plugin PR shows the checklist
- **WHEN** a contributor opens a PR that adds a plugin
- **THEN** the PR description lists the required checks and the two questions, and has no checkbox for a property a required check enforces

## ADDED Requirements

### Requirement: Verified tier is decided by evidence

A plugin SHALL have tier `verified` only when it meets every community criterion and also:
- ships trigger query sets for each skill and narrow eval tasks in the `rf-skill-eval` harness;
- has committed eval baselines measured on the current models, and passes the eval gate;
- passes the security gate and the library-skill keyword check.

The tier check SHALL decide from this evidence alone. It SHALL NOT require a number of maintainers or membership of a team. A bundle is `verified` when every plugin it bundles is.

#### Scenario: Verified without evals is refused
- **WHEN** a PR sets `tier: verified` for a plugin that has no trigger sets
- **THEN** the tier check fails and names the missing evidence

#### Scenario: One maintainer is enough
- **WHEN** a `verified` plugin has one maintainer and all the evidence above
- **THEN** the tier check passes

### Requirement: Review is one maintainer approval, and checks do the rest

The maintainers of the repository are the people with the Maintain or Admin role on it. `main` SHALL be protected so that:
- every required status check passes before a PR merges, with no bypass for anyone;
- a PR needs one approval from a code owner, and `CODEOWNERS` SHALL name the maintainers as the default owner of every path;
- a maintainer MAY merge their own PR without an approval once every required check passes, through the PR (never by a direct push).

A plugin's maintainers listed in `catalog.yaml` are the people who answer for it (see `plugin-lifecycle`). Their approval SHALL NOT be required, because GitHub only counts approvals from people with write access.

#### Scenario: Maintainer PR merges on green checks
- **WHEN** a maintainer opens a PR that edits `plugins/rf-core/hooks/hooks.json` and every required check passes
- **THEN** the maintainer can merge it without another person's approval

#### Scenario: External PR needs one maintainer
- **WHEN** a contributor without write access opens a PR that adds `plugins/rf-mind/`, and every required check passes
- **THEN** the PR can't merge until one maintainer approves it

#### Scenario: Failing check blocks everyone
- **WHEN** the security gate fails on a maintainer's PR
- **THEN** the PR can't be merged, by the maintainer or anyone else

### Requirement: No governance check fails because of the date

The ownership and tier checks SHALL give the same result for the same repository tree on any date. Exceptions with an end date SHALL NOT exist in the governance configuration. (Security baseline expiry is a separate, deliberate re-review; see `content-security-scanning`.)

#### Scenario: Same tree, later date
- **WHEN** the tier check runs on the same commit on 2026-11-16 and on 2027-02-01
- **THEN** both runs give the same result

## REMOVED Requirements

### Requirement: Verified tier entry criteria

**Reason**: It asks for two maintainers, one of them in a Foundation reviewers team that doesn't exist, and for a Foundation reviewer's approval of the promotion. Under this change the tier is decided by evidence alone.

**Migration**: Replaced by "Verified tier is decided by evidence". The evidence (trigger sets, narrow tasks, baselines, eval gate) stays; the security gate and the keyword check are named explicitly; the maintainer count, team membership and approval for the promotion are dropped.

### Requirement: Every change is reviewed by an owner of the plugin

**Reason**: It needs a Foundation reviewers team and a security reviewers team, which don't exist. A custom `required-reviews` check enforces it, and no PR touching a plugin has passed that check without the admin bypass. It also asks for approvals from plugin maintainers who have no write access, which GitHub can't count.

**Migration**: Replaced by "Review is one maintainer approval, and checks do the rest". The `required-reviews` status, its workflows and `.github/governance.yaml` are removed. The ruleset requires one code-owner approval instead, and maintainers bypass it for their own PRs. Security-relevant paths are guarded by the security gate (`content-security-scanning`).
