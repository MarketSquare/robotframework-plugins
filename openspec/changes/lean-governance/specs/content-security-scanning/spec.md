## MODIFIED Requirements

### Requirement: Every content type is in scope

The security checks SHALL cover these content types in every plugin: `SKILL.md` files, skill references and assets, subagent definitions in every agent format (Markdown and the Codex TOML variant), hook configuration and hook scripts, helper scripts, MCP server configuration, and plugin and marketplace manifests. Hooks, scripts, MCP configuration, subagent `tools` lists, skill `allowed-tools` and manifests SHALL count as security-relevant content. A change to them SHALL pass the security gate like any other change; it SHALL NOT need an approval from a separate security team.

#### Scenario: A subagent is scanned
- **WHEN** a PR changes only `plugins/<name>/agents/<agent>.md`
- **THEN** the PR gate scans that file for prompt injection, credential access and data exfiltration patterns

### Requirement: The gate fails on new findings only

Each plugin SHALL have a reviewed baseline of accepted findings, at `security/baselines/<plugin>.yaml`. Each entry SHALL record the scanner, the rule, the file, a reason and an expiry date no more than 12 months away. The gate SHALL fail on any HIGH or CRITICAL finding that is not in the baseline, and on any baseline entry that has expired. It SHALL report MEDIUM and lower findings without failing. The PR gate SHALL list entries that expire within 30 days as warnings. The scheduled scan of `main` SHALL fail on them, so that a maintainer renews or removes an entry before it blocks a PR.

#### Scenario: Known false positive does not fail
- **WHEN** a skill's reference warns against `sudo pip install` and SkillSpector flags it, and the finding is in the baseline with a reason
- **THEN** the gate passes and lists the finding as accepted

#### Scenario: Expired baseline entry
- **WHEN** a baseline entry's expiry date has passed
- **THEN** the gate fails until the entry is renewed with a new review or removed

#### Scenario: Expiry is flagged ahead
- **WHEN** a baseline entry expires in 20 days
- **THEN** the PR gate passes with a warning naming the entry, and the scheduled scan of `main` fails naming it

### Requirement: Model-assisted scans run only after maintainer approval

Scans that send plugin content to a model provider SHALL run only when a maintainer starts them for a PR by its number, or on pushes to `main`. They SHALL NOT use the `pull_request_target` event. They SHALL treat PR content as data and SHALL NOT execute it. When the maintainer names the reviewed head commit, the scan SHALL refuse a PR whose head has moved on. For a PR, the findings SHALL be posted as a comment, and a new HIGH or CRITICAL finding SHALL set a failing `security-deep-scan` status. On `main`, the model findings SHALL be reported in the run summary without failing the run, because they change between runs and can't be baselined; the run SHALL fail only when a scan stops before writing its summary.

#### Scenario: Unlabelled fork PR
- **WHEN** a maintainer has not started the scan for a fork PR
- **THEN** no plugin content from it is sent to a model provider

#### Scenario: The PR moved on after the review
- **WHEN** a maintainer starts the scan with the reviewed head commit and the contributor has pushed since
- **THEN** the run stops before sending anything to the model and names both commits

#### Scenario: A model finding on main
- **WHEN** the model pass reports a new HIGH finding during the push run on `main`
- **THEN** the run passes with a warning, and the finding is listed in the run summary

## ADDED Requirements

### Requirement: Repository-level secret protection

The repository SHALL have GitHub secret scanning and push protection enabled, so that a push containing a recognised secret is blocked before it lands. Dependabot security updates SHALL be enabled for the repository's dependency manifests.

#### Scenario: Secret in a push
- **WHEN** someone pushes a commit that contains a recognised API key to any branch of the repository
- **THEN** GitHub blocks the push and names the secret type
