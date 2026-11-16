## Why

Robot Framework agent plugins currently live in one personal repository (`manykarim/robotframework-agentskills`) with one author. The Robot Framework Foundation wants a proper skills programme under MarketSquare. A pile of contributed Markdown files is not enough: the programme needs clear quality bars, visible trust levels, security checks on every kind of content, easy installation on every agent, named owners with a deprecation path, and evidence of which plugins actually help. The new repository `MarketSquare/robotframework-plugins` exists and is empty, so the move and the programme rules can land together before other contributors arrive.

## What Changes

- **Move the code.** Copy `robotframework-agentskills` into `MarketSquare/robotframework-plugins` with its full git history and release tags, grafted onto the repository's initial commit. `rf-agentskills` becomes the first plugin of the new marketplace.
- **BREAKING:** The marketplace is renamed from `robotframework-agentskills` (GitHub source `manykarim/robotframework-agentskills`) to `robotframework-plugins` (GitHub source `MarketSquare/robotframework-plugins`). Install commands change, so users re-add the marketplace. The installer migrates project settings that use the old marketplace entry.
- **BREAKING:** The installer is published to PyPI as `robotframework-plugins`, with the command `robotframework-plugins`. A final `rf-agentskills` release on PyPI depends on the new package and forwards to it with a deprecation notice.
- **Versions with one source each.** Each plugin has its own SemVer version, set only in its `plugin.json` and tagged `<plugin>--v<version>` (Claude Code's convention). The installer uses calendar versions (`YYYY.M.PATCH`), because each release is a snapshot of the catalogue. A generated table shows which plugin versions each installer release bundles.
- **One repo, many plugins.** All plugins live under `plugins/<name>/` in this repository, each with its own sources, tests and evals; the root `skills/` copy and its sync step go away. Skill and subagent names are unique across the catalogue. Each plugin carries a programme manifest (`plugins/<name>/catalog.yaml`) giving its purpose, maintainers, tier, status, supported libraries and versions, and supported agents. The README catalogue and `robotframework-plugins list` are generated from these manifests. The installer can install a chosen set of plugins.
- **Trust tiers.** Each plugin is either `verified` or `community`, with written entry criteria and a lightweight review: CODEOWNERS per plugin, a review checklist, and approval by a Foundation reviewer for the verified tier.
- **Security checks for all content.** Skills, references, subagents, hooks, scripts, MCP configuration and manifests are all treated as instructions that can act. Every PR, including PRs from forks, runs static checks without secrets: the house checks, Cisco skill-scanner, SkillSpector without its model pass, cc-audit for MCP and plugin manifests, and Gitleaks. The gate fails on new HIGH or CRITICAL findings that are not in a reviewed baseline. Model-assisted scans run after a maintainer applies a label. Live `rf-skill-eval` runs happen only on maintainer branches and after merge.
- **Lifecycle.** Rules for ownership and maintenance expectations, a path from active to deprecated to removed, and demotion of unmaintained verified plugins.
- **Adoption without telemetry.** The installer sends nothing. A quarterly adoption report is built from public signals: PyPI downloads, GitHub traffic, per-plugin feedback issues and eval score trends.
- **Documentation in the Robot Framework Voice.** README, CONTRIBUTING, GOVERNANCE, SECURITY, the plugin template and the installer README.
- **Wind down the old home.** The old README gets a "moved" notice, existing marketplace pins keep working (the repository is archived, not deleted), and the old PyPI package ends with the forwarding release.

## Capabilities

### New Capabilities
- `repository-migration`: copying with history and tags, the rename map, what stays named `rf-agentskills`, and winding down the old repository and PyPI package.
- `plugin-catalogue`: the per-plugin `catalog.yaml` manifest, the generated catalogue, and installing a chosen set of plugins from the one marketplace.
- `plugin-trust-tiers`: entry criteria for `verified` and `community` plugins, the review process, CODEOWNERS, and how a tier is shown to users.
- `content-security-scanning`: what counts as security-relevant content (every content type), the PR-gate scanners, the reviewed-baseline rule, label-triggered model scans, and limits on running untrusted plugin content in CI.
- `plugin-lifecycle`: ownership, maintenance expectations, deprecation and removal, and demotion of unmaintained plugins.
- `adoption-reporting`: public, opt-in signals and the quarterly report; no installer telemetry.
- `programme-documentation`: the required documents and the Robot Framework Voice rules they follow.

### Modified Capabilities
- `agent-plugin-marketplace`: the marketplace name, owner and GitHub source change; the marketplace lists several plugins with tier tags; versions are set only in `plugin.json` and releases are tagged per plugin; scenario counts are corrected to 9 skills and 3 subagents.
- `skill-catalog`, `skill-metadata-conformance`, `skill-content-verification`, `library-skill-install-guidance`, `library-skill-structure`, `setup-skill`, `platynui-skill`: the root `skills/` source and its sync step are replaced by per-plugin sources; `metadata.version` follows the plugin's version.
- `installer-onboarding`: the PyPI zero-install entry point becomes `robotframework-plugins`, published with trusted publishing; `rf-agentskills` remains as a forwarding package.
- `installer-plugin-bootstrap`: project settings use the `robotframework-plugins` marketplace entry and source, the Codex commands change, and old marketplace entries are migrated on reinstall.

## Impact

- **Repositories:** `MarketSquare/robotframework-plugins` receives the full tree and history. `manykarim/robotframework-agentskills` gets a final notice commit and is then archived.
- **Packages:** a new PyPI project `robotframework-plugins`, and a final forwarding release `rf-agentskills` 0.9.0. `robotframework-plugins` starts at the calendar version of the month it ships, for example `2026.12.0`. The Python module is renamed from `rf_agentskills` to `robotframework_plugins`. The `rf-skill-eval` harness stays internal and keeps its name.
- **Users:** marketplace install commands and pinned refs change to the new source. Plugin and skill names are unchanged, so skills keep their invocation names.
- **CI:** new workflows for the security PR gate (SARIF reports as artifacts and in the job summary), label-triggered model scans, trusted publishing to PyPI and catalogue generation. Existing CI, eval and release workflows move over with updated names.
- **Governance:** a GitHub team for Foundation reviewers and a security reviewer group must exist in the MarketSquare organisation, and a PyPI trusted publisher must be configured for the new project.
- **Docs:** README, CONTRIBUTING.md, GOVERNANCE.md, SECURITY.md, the plugin template, `RELEASING.md` and the installer README are written or rewritten.
