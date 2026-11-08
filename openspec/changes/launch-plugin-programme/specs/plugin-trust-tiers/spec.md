## Purpose

Defines the two trust tiers of the programme, `verified` and `community`, the evidence each tier requires, and the lightweight review that admits a plugin or a change to it, so users can tell Foundation-verified plugins from community contributions.

## ADDED Requirements

### Requirement: Community tier entry criteria

A plugin SHALL be admitted with tier `community` only when all of the following hold:
- a valid `catalog.yaml` with at least one maintainer;
- every content type passes the PR security gate (see `content-security-scanning`);
- every skill passes the house static checks: frontmatter conformance, description length, links resolve, `.robot` examples parse with a dry run;
- every skill and subagent states its purpose and its supported libraries and versions;
- a README for the plugin.

#### Scenario: Community plugin without examples that parse
- **WHEN** a community plugin's skill ships a `.robot` example that fails the dry run
- **THEN** the PR check fails and the plugin is not merged

### Requirement: Verified tier entry criteria

A plugin SHALL have tier `verified` only when it meets every community criterion and also:
- has at least two maintainers, at least one of them a member of the Foundation reviewers team;
- ships trigger query sets for each skill and eval tasks in the `rf-skill-eval` harness;
- has committed eval baselines measured on the current models, and passes the eval gate;
- has been approved for the verified tier by a Foundation reviewer, recorded in the PR that sets `tier: verified`.

#### Scenario: Verified without evals is refused
- **WHEN** a PR sets `tier: verified` for a plugin that has no trigger sets
- **THEN** the tier check fails and names the missing evidence

#### Scenario: Tier promotion needs a Foundation reviewer
- **WHEN** a PR changes `tier` from `community` to `verified` and only non-Foundation maintainers approve it
- **THEN** the PR cannot be merged

### Requirement: Every change is reviewed by an owner of the plugin

`.github/CODEOWNERS` SHALL map each `plugins/<name>/` to that plugin's maintainers. A change to a plugin SHALL require approval by one of its code owners. A change to a `verified` plugin SHALL also require approval by a Foundation reviewer. A change to security-relevant content (see `content-security-scanning`) SHALL require approval by the security reviewers team. CI SHALL fail when CODEOWNERS and the `maintainers` in `catalog.yaml` disagree.

#### Scenario: Hook change needs the security team
- **WHEN** a PR edits `plugins/rf-agentskills/hooks/hooks.json`
- **THEN** merging requires an approval from the security reviewers team as well as a plugin owner

#### Scenario: CODEOWNERS drift
- **WHEN** a maintainer is added to `catalog.yaml` but not to CODEOWNERS
- **THEN** the ownership check fails

### Requirement: Review follows a published checklist

Every plugin PR SHALL use a PR template whose checklist covers purpose, supported versions, examples, security-relevant changes, tool permissions and documentation voice. A reviewer SHALL NOT approve a PR with an unchecked checklist item unless the item is marked as not applicable with a reason.

#### Scenario: New plugin PR shows the checklist
- **WHEN** a contributor opens a PR that adds a plugin
- **THEN** the PR description contains the review checklist
