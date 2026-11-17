## Context

See proposal.md (Why). What this change builds on:

- `CONTRIBUTING.md` (173 lines) already has a table of PR checks with their commands. The same commands run in `.github/workflows/ci.yml`: `build-catalog.py --check`, `check-governance.py`, `check_content_rules.py`, `validate-skills.py`, `check-plugin-references.py`, `check-drift.sh`, `check-docs-voice.py`, and `pytest tests/ --ignore=tests/eval` plus each plugin's tests. The harness tests run with `uv sync --all-extras && uv run pytest tests/eval/` (`ci.yml:122`).
- `scripts/check-docs-voice.py` checks the top-level `*.md` files, so new top-level documents are covered without a change.
- `.gitignore` doesn't ignore `CLAUDE.md` or `AGENTS.md`, and neither file exists in the repository.
- `openspec/config.yaml` sets only `schema: spec-driven`.
- RobotCode's `AI_POLICY.md` (robotcodedev/robotcode, main) is the model for the policy. RobotCode's "Working with AI Agents" guide and its chat plugin already teach agents to use the CLI, and our skills hand CLI usage to that plugin.
- The CLI guide (https://robotcode.io/guides/cli/) has these pages:
  - Discovering Tests (`discover`)
  - Analyzing Code (`analyze code`)
  - Analyzing Results (`results`)
  - REPL (`repl`)
  - Debugging (`robot-debug`)
  - Browsing Documentation (`doc`)
  - Wrapper (`--wrapper`)
  - the `robot.toml` page for `robot`/`run`, and Troubleshooting for `config`/`profiles`

## Goals / Non-Goals

**Goals:**
- One short text that a coding agent can follow to make a PR that passes CI the first time.
- A policy that says what AI-assisted contributions must meet, adapted to a repository whose output is itself agent content.
- RobotCode as the shared base for Robot Framework capabilities, written down where contributors and OpenSpec proposals see it.
- Checks that fail when the guide and CI drift apart, so the guide doesn't need a reviewer to keep it true.

**Non-Goals:**
- Changing the repository's own tooling to follow the RobotCode-first rule: that is `robotcode-first-tooling`.
- Changing review rules: that is `lean-governance`. This change links to `GOVERNANCE.md` and doesn't restate the rules.
- Detecting AI-written PRs automatically. Disclosure relies on the contributor.
- Removing stale documents: that is `repo-cleanup`.

## Decisions

### D1. Two documents: a policy and an operational guide

`AI_POLICY.md` is for people. It explains what is expected and why, and follows the structure of RobotCode's policy (human responsibility, disclosure, licensing, communication, PRs, low-context submissions, enforcement), with a section for what is specific to this repository. `AGENTS.md` is for agents. It is a list of facts and commands, kept under about 120 lines, that links to the policy instead of repeating it.

Alternative: one file. It would mix rules for people with command lists for agents, and the agent part would grow into a second CONTRIBUTING.md.

### D2. `CLAUDE.md` imports `AGENTS.md`

`CLAUDE.md` contains `@AGENTS.md` and nothing else. Claude Code expands the import. Codex, Copilot, Cursor and OpenCode read `AGENTS.md` directly. One text serves every agent we support.

Alternatives:
- A symlink. Plugins avoid symlinks, and Windows checkouts handle them badly.
- A copy. It would drift.

### D3. The RobotCode-first rule and its capability map live in `AGENTS.md`; the policy states the rule

The rule is stated in full in both documents: it is a policy, and agents need it in context. The capability map (need → `robotcode` command → guide page link) appears only in `AGENTS.md`, because only agents act on it. It links the guide pages rather than copying their options, so it stays correct when RobotCode adds flags.

The rule says what "re-implement" means in practice: our own code that parses Robot Framework files to resolve keywords, runs `robot` and parses `output.xml` for results, or builds libdoc output to look up keywords, when a `robotcode` command gives the same answer. Custom code that calls `robotcode` and adds project-specific logic is fine.

### D4. The guide is checked against CI, not reviewed

`tests/test_contributor_guidance.py`:
- **Section parsing.** It reads the "Checks" section of `AGENTS.md` (one command per bullet, in backticks) and asserts that each command string occurs in `.github/workflows/ci.yml`, ignoring whitespace differences.
- **Paths.** It asserts that every `scripts/<file>` named anywhere in `AGENTS.md` exists.
- **`CLAUDE.md`.** It asserts the file's only non-blank line is `@AGENTS.md`.
- **Templates.** It asserts the PR template has an "AI assistance" heading and the RobotCode checklist item, and that the issue template mentions disclosure.

When `lean-governance` or `repo-cleanup` removes a script or a CI step, this test makes them update `AGENTS.md` in the same PR.

### D5. OpenSpec context and rules

`openspec/config.yaml` gets a `context` block of about 20 lines:
- what the repository ships;
- the top-level layout;
- the RobotCode-first rule in two sentences;
- "write for people in the Robot Framework Voice; see CONTRIBUTING.md".

It gets two rules, one for `proposal` and one for `tasks`, as listed in the proposal. The context is plain facts, so it doesn't go stale faster than `AGENTS.md`; the test in D4 doesn't check it, because OpenSpec reads it only when a change is drafted.

### D6. CONTRIBUTING.md keeps its required sections and drops duplicates

`programme-documentation` requires a "Versions" section in `CONTRIBUTING.md`, so it stays.
- The "Review" section shrinks to two sentences and a link to `GOVERNANCE.md`, which `lean-governance` rewrites.
- The layout block gains `legacy/` (the one-shot `rf-agentskills` forwarder) and `openspec/`, and says that `bundles/rf-agentskills/` is generated from the plugins listed in `plugins/rf-agentskills/catalog.yaml`.
- A new first paragraph links `AGENTS.md` for agents and `AI_POLICY.md` for anyone using AI tools.

## Risks / Trade-offs

- [The guide drifts on things the test can't see, such as the layout or the OpenSpec steps] → It's kept short, and `repo-cleanup` removes the material that changes most often. A stale line costs a failed CI run, not a wrong release.
- [The RobotCode-first rule blocks a contribution where `robotcode` is close but not good enough] → The rule allows a custom script that names the upstream issue it bridges, and maintainers decide.
- [Disclosure can't be enforced] → The template asks for it every time, and the policy lets maintainers close low-context PRs. As at RobotCode, the aim is honest contributors, not detection.
- [`@AGENTS.md` import syntax changes in Claude Code] → The test pins the one-line form; a change shows up as a failing test, not a silent gap.
