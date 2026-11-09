# Governance

How plugins get in, who reviews what, what maintainers commit to, and how a plugin is deprecated, demoted or removed.

## Tiers

Every plugin is `community` or `verified`. The tier is in its `catalog.yaml` and in the catalogue.

### community

A plugin enters as `community` when:

- its `catalog.yaml` is valid and names at least one maintainer;
- it passes the security gate (house content rules, scanners, reviewed baseline);
- every skill passes the static checks: frontmatter, description length, links that resolve, `.robot` examples that pass a dry run;
- every skill and subagent states its purpose and the libraries and versions it supports;
- it has a README.

### verified

A `verified` plugin meets every community criterion and also:

- has at least two maintainers, one of them in the Foundation reviewers team;
- ships trigger query sets for each skill and eval tasks in the `rf-skill-eval` harness;
- has eval baselines measured on the current models, and passes the eval gate;
- was approved for the tier by a Foundation reviewer, in the PR that sets `tier: verified`.

`scripts/check-governance.py` checks the evidence in CI. A plugin that lacks some of it can stay `verified` only under a dated entry in `.github/governance.yaml`, which names what's missing; after the date, the check fails. The launch plugins have such an entry until 2027-01-31, for their second maintainer.

### What a tier doesn't promise

A tier describes the evidence behind a plugin. It isn't a warranty: the checks and reviews make a harmful or broken plugin less likely, and they can't rule one out. See [SECURITY.md](SECURITY.md).

## Review

Every change to a plugin needs an approval from one of its maintainers (listed in `catalog.yaml` and `.github/CODEOWNERS`, which must agree). On top of that:

| The PR | also needs |
|---|---|
| changes a `verified` plugin, or promotes one to `verified` | a Foundation reviewer (`@MarketSquare/robotframework-plugins-reviewers`) |
| changes security-relevant content: hooks, scripts, MCP configuration, manifests, subagent `tools`, skill `allowed-tools`, workflows, `security/` | a security reviewer (`@MarketSquare/robotframework-plugins-security`) |

The `required-reviews` check enforces this; the author's own approval doesn't count. Reviewers work through the checklist in the PR template and don't approve while an item is unticked without a reason.

## What maintainers commit to

- A first response to issues labelled for their plugin within **14 days**.
- A first response to security reports about their plugin within **7 days**.
- A compatibility check of their plugin within **60 days** of each Robot Framework major release, and of each major release of a library listed in their `catalog.yaml`.

## Lifecycle

### Deprecation

To deprecate a plugin, a PR:

- sets `status: deprecated`, `deprecated_since` (the date) and `replacement` (a plugin, or a sentence when there is none) in `catalog.yaml`;
- adds a deprecation notice to the top of the plugin's README.

The next release notes list it. A deprecated plugin stays installable and is tagged `deprecated` in the marketplace.

### Removal

A plugin can be removed once it has been deprecated for at least **two installer releases** and **90 days**; `scripts/build-catalog.py --check` refuses an earlier removal and names the earliest release and date. Removing it sets `status: removed`, maps its name to `null` in the marketplace `renames`, and is listed in the release notes of the installer release that stops bundling it. Claude Code then uninstalls it (`forceRemoveDeletedPlugins`), and the Python installer removes its files on the next upgrade, keeping and reporting files the user changed.

### Demotion

- A `verified` plugin whose maintainers miss the response targets for 90 days, or that fails the eval gate for two consecutive releases of the plugin, moves to `community`.
- A `community` plugin with no maintainer response for 180 days is deprecated.

Each demotion is a PR that states the reason and stays open for at least 14 days before it is merged. The release notes list the tier change. The quarterly adoption report (`docs/reports/`) lists candidates; a candidate is a prompt for this decision, not the decision.

### Handing over

A maintainer steps down with a PR that removes them from `catalog.yaml` and CODEOWNERS. A plugin left without maintainers is deprecated unless a new maintainer is added within 30 days; the catalogue check refuses an active plugin with nobody listed.
