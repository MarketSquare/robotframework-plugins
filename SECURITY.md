# Security

## Report a vulnerability

Use GitHub's private vulnerability reporting: on the repository's **Security** tab, choose **Report a vulnerability**. Please don't open a public issue for it.

You'll get a first response within **7 days**. Tell us the plugin and version, the agent you used, what happens, and the steps to reproduce it.

Report here:

- a plugin that makes an agent do something you didn't ask for: run commands, read secrets, send data out, change files outside the task;
- a hook or script that can be made to run unintended commands;
- a weakness in the installer, the security checks or the CI workflows.

## What runs on your machine

Plugins are instructions and code for an agent that can run commands with your permissions. Skills and subagents tell the agent what to do; hooks and scripts run directly when the agent edits files or finishes a task. Read what you install, as you would any other dependency.

The installer, hooks and scripts send nothing anywhere: no usage data, no identifiers, no content. The installer only touches the network for the marketplace and package operations you ask for.

## What the checks cover

Every pull request, including those from forks, runs a security gate without secrets:

- the house content rules (`scripts/check_content_rules.py`): hidden Unicode characters, HTML comments in skills and subagents, subagents without an explicit tool list, unrestricted shell access in `allowed-tools`, downloads piped into a shell, MCP servers without an exact version;
- Cisco skill-scanner, SkillSpector (without its model pass), cc-audit and Gitleaks, at pinned versions;
- a comparison with each plugin's reviewed baseline: a new HIGH or CRITICAL finding fails the PR.

Scans that send content to a model run only after a maintainer applies the `security-deep-scan` label, and on the main branch. Live agent evaluations, which run plugin hooks with an API key, never run code from forks. Changes to hooks, scripts, MCP configuration, manifests, tool permissions and the baselines need an approval from the security reviewers.

## What the checks can't promise

Passing the checks and the review doesn't prove a plugin is safe. Scanners match patterns and miss what they don't know; an instruction can be harmful in plain words; a reviewer can overlook something. A plugin's tier ([GOVERNANCE.md](GOVERNANCE.md)) describes the evidence behind it, not a warranty.
