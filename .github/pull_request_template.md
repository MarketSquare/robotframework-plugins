## What this changes

<!-- One or two sentences: what a user of the plugin gets from this PR. -->

## Review checklist

Tick each item, or write "n/a: <reason>" after it. Reviewers don't approve a PR
with an unticked item that has no reason (see CONTRIBUTING.md, "Review").

- [ ] **Purpose.** Each new or changed skill and subagent says what it is for and when to use it, in its description.
- [ ] **Supported versions.** `catalog.yaml` lists the libraries and version ranges the content was checked against, and the Robot Framework range.
- [ ] **Examples.** `.robot` examples pass `robot --dryrun`; Python examples run.
- [ ] **Security-relevant changes.** Hooks, scripts, MCP configuration, manifests, subagent `tools` and skill `allowed-tools` changes are listed below; the security gate passes, and any new baseline entry has a reason.
- [ ] **Tool permissions.** Every subagent declares an explicit `tools` list; no `allowed-tools` entry grants unrestricted shell access.
- [ ] **Documentation voice.** Text follows the writing rules in CONTRIBUTING.md and passes the docs voice check.

### Security-relevant changes

<!-- List them, or write "none". -->
