## Why

Much of the work on this repository is done with coding agents, and the content it ships (skills, hooks, subagents, scripts) is read and run by other people's agents. Yet nothing tells a contributor, human or AI, how AI-assisted work is accepted, which local checks to run, which files are generated, or which tool to build on for Robot Framework capabilities. `openspec/config.yaml` gives proposals no project context either. The result is AI-written changes that re-implement what RobotCode already does, hand-edit generated files, or fail CI on checks nobody ran (PR #20 failed a repository check that was never run locally).

## What Changes

- **`AI_POLICY.md`** (new), adapted from RobotCode's AI policy:
  - from RobotCode's policy: a human owns, understands and tests every change; AI use is disclosed in the PR or issue, with an optional `AI-Assisted-By:` commit trailer; the contributor confirms the right to submit under Apache-2.0; low-context automated submissions are declined; maintainers decide;
  - specific to this repository:
    - skill, hook, subagent and script content is security-relevant, because other people's agents read and run it;
    - every keyword a skill teaches must resolve (`scripts/check-skill-keywords.py`);
    - generated files are never edited by hand: name the command that regenerates them;
    - paid eval runs and re-baselines are dispatched by maintainers;
    - eval tasks and fixtures read like real user requests and real projects;
  - the **RobotCode-first rule** (below).
- **The RobotCode-first rule.**
  - The `robotcode` CLI (https://robotcode.io/guides/cli/) is the core of the Robot Framework AI toolstack.
  - AI solutions in this repository use it to run, discover, analyse, inspect results, run keywords step by step in the REPL, look up keywords and debug, instead of new custom implementations.
  - Gaps go upstream to RobotCode, the central place for such improvements.
  - Custom scripts (hooks, skill helpers, eval grading) are fine when they don't re-implement those capabilities.

  The rule comes with a capability map: need → command → guide page. Enforcing it in the repository's own tooling is the separate change `robotcode-first-tooling`.
- **`AGENTS.md`** (new): a short operational guide for coding agents. It covers:
  - the layout;
  - the exact local checks, the same commands CI runs;
  - generated files and how to regenerate them;
  - files never to commit;
  - the OpenSpec workflow;
  - links to `AI_POLICY.md` and the RobotCode-first rule.

  **`CLAUDE.md`** (new) contains only `@AGENTS.md`, so Claude Code loads the same text.
- **PR template.** Add an AI-disclosure section and a checklist item: "Robot Framework capabilities go through `robotcode`; gaps are reported upstream". The issue template gets a disclosure note.
- **`openspec/config.yaml`.**
  - Add `context` with the project summary, the layout, the RobotCode-first rule and the docs voice.
  - Add `rules`:
    - a proposal that touches Robot Framework capabilities says which `robotcode` command it uses, or why none fits;
    - every task has a verify clause.
- **`CONTRIBUTING.md`.**
  - Fix the layout: add `legacy/` and `openspec/`, and say that `bundles/` is generated from `plugins/rf-agentskills/catalog.yaml`.
  - Replace the review-group list with a link to `GOVERNANCE.md`, which the change `lean-governance` rewrites.
  - Link `AGENTS.md` and `AI_POLICY.md`. The README links them too.
- **Automated checks.** A repository test asserts:
  - `AGENTS.md` and `AI_POLICY.md` exist;
  - every script `AGENTS.md` names exists, and every check command in it appears in `.github/workflows/ci.yml`;
  - `CLAUDE.md` imports `AGENTS.md`;
  - the PR template has the disclosure section and the RobotCode item.

  `scripts/check-docs-voice.py` already covers top-level `*.md` files, so the new documents get the voice check.

## Capabilities

### New Capabilities
- `contributor-guidance`: the AI contribution policy, the RobotCode-first rule, the agent guide, the PR template items, the OpenSpec project context, and the checks that keep them consistent with CI.

### Modified Capabilities

None. `programme-documentation` (added by the unarchived change `launch-plugin-programme`) keeps its requirements. This change adds its own documents next to them and doesn't move the "Versions" section, which that capability requires in `CONTRIBUTING.md`.

## Impact

- **New files:** `AI_POLICY.md`, `AGENTS.md`, `CLAUDE.md`, and a test `tests/test_contributor_guidance.py`.
- **Changed files:** `.github/pull_request_template.md`, `.github/ISSUE_TEMPLATE/plugin-feedback.yml`, `openspec/config.yaml`, `CONTRIBUTING.md` and `README.md`.
- **No change to:** code, plugins, the installer, the release or the evals.
- **Related changes:**
  - `repo-cleanup` removes the stale material `AGENTS.md` would otherwise have to warn about.
  - `lean-governance` owns the review rules this change links to.
  - `robotcode-first-tooling` applies the RobotCode-first rule to the repository's own scripts.
- **Contributors:** a PR with substantial AI help needs a disclosure line. Small fixes don't.
