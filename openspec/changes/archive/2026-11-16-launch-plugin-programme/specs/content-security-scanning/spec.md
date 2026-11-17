## Purpose

Treats every piece of plugin content as instructions that can make an agent act, and defines the automated checks, the reviewed-baseline rule and the CI trust boundaries that apply to skills, references, subagents, hooks, scripts, MCP configuration and manifests alike.

## ADDED Requirements

### Requirement: Every content type is in scope

The security checks SHALL cover these content types in every plugin: `SKILL.md` files, skill references and assets, subagent definitions in every agent format (Markdown and the Codex TOML variant), hook configuration and hook scripts, helper scripts, MCP server configuration, and plugin and marketplace manifests. The following SHALL count as security-relevant content and need security-team review (see `plugin-trust-tiers`): hooks, scripts, MCP configuration, subagent `tools` lists, skill `allowed-tools`, and manifests.

#### Scenario: A subagent is scanned
- **WHEN** a PR changes only `plugins/<name>/agents/<agent>.md`
- **THEN** the PR gate scans that file for prompt injection, credential access and data exfiltration patterns

### Requirement: House content rules

The PR gate SHALL fail, independent of external scanners, when shipped content contains any of the following:
- Unicode tag characters (U+E0000 to U+E007F) or zero-width characters outside code blocks that document them;
- HTML comments in `SKILL.md` files or subagent definitions;
- a subagent without an explicit `tools` list, which inherits every tool, or with a `tools` value of `*`;
- an `allowed-tools` entry that grants unrestricted shell access;
- a shipped script or hook that pipes downloaded content into a shell or an interpreter;
- a shipped MCP configuration that starts a package without an exact version.

#### Scenario: Hidden Unicode instruction
- **WHEN** a reference file contains characters from the Unicode tag block
- **THEN** the gate fails and reports the file and line

#### Scenario: Wildcard subagent tools
- **WHEN** a subagent declares `tools: "*"`, or declares no `tools` list
- **THEN** the gate fails and names the subagent

### Requirement: Static scanners gate every PR without secrets

Every PR, including PRs from forks, SHALL run a static security job that has no repository secrets and no write permissions, and that does not execute plugin content. The job SHALL run, at pinned versions with verified checksums:
- Cisco skill-scanner on changed skills and, in lenient mode, on changed subagents and on each changed plugin's whole shipped tree, which is the pass that reads hooks and scripts;
- SkillSpector with the model pass disabled on changed skills and subagents;
- cc-audit on MCP configuration and manifests;
- Gitleaks on the PR diff.

Findings SHALL be published as SARIF files in the job artifacts and summarised in the job summary.

#### Scenario: Fork PR runs the gate
- **WHEN** a contributor opens a PR from a fork
- **THEN** the static security job runs to completion without access to repository secrets

#### Scenario: Planted exfiltration in a hook script
- **WHEN** a PR adds a hook script line that sends `process.env` to a remote URL
- **THEN** the gate reports a HIGH or CRITICAL finding on that file and fails

### Requirement: The gate fails on new findings only

Each plugin SHALL have a reviewed baseline of accepted findings, at `security/baselines/<plugin>.yaml`. Each entry SHALL record the scanner, the rule, the file, a reason and an expiry date no more than 12 months away. The gate SHALL fail on any HIGH or CRITICAL finding that is not in the baseline, and on any baseline entry that has expired. It SHALL report MEDIUM and lower findings without failing. Changes to a baseline file SHALL require approval by the security reviewers team.

#### Scenario: Known false positive does not fail
- **WHEN** a skill's reference warns against `sudo pip install` and SkillSpector flags it, and the finding is in the baseline with a reason
- **THEN** the gate passes and lists the finding as accepted

#### Scenario: Expired baseline entry
- **WHEN** a baseline entry's expiry date has passed
- **THEN** the gate fails until the entry is renewed with a new review or removed

### Requirement: Model-assisted scans run only after maintainer approval

Scans that send plugin content to a model provider SHALL run only when a maintainer applies the `security-deep-scan` label to a PR, or on pushes to `main`. They SHALL treat PR content as data and SHALL NOT execute it. Their findings SHALL be posted to the PR as a comment and SHALL block merge when they report a new HIGH or CRITICAL finding.

#### Scenario: Unlabelled fork PR
- **WHEN** a fork PR has not been labelled
- **THEN** no plugin content from it is sent to a model provider

### Requirement: Untrusted plugin content is never executed with secrets

Live agent evaluations (`rf-skill-eval`), which run plugin hooks and scripts, SHALL run only on commits that are on `main` or on branches pushed by maintainers. They SHALL NOT run on fork PR code in a context that has access to secrets.

#### Scenario: Fork PR does not trigger live evals
- **WHEN** a fork PR changes a hook script
- **THEN** no live evaluation runs that PR's code with an API key

### Requirement: Security policy and reporting

The repository SHALL contain `SECURITY.md` explaining how to report a vulnerability privately (GitHub private vulnerability reporting), the response target (first response within 7 days), and what the automated checks cannot guarantee.

#### Scenario: Reporter finds the channel
- **WHEN** a user opens the repository's Security tab
- **THEN** the policy and a private reporting option are shown
