## 1. Policy (D1, D3)

- [x] 1.1 Write `AI_POLICY.md`, following the sections of RobotCode's policy (human responsibility, disclosure, licensing and right to submit under Apache-2.0, issues and comments, pull requests, low-context submissions, enforcement), plus a section "In this repository" with the security, keyword, generated-file, eval-dispatch and realistic-eval rules, and the RobotCode-first rule; verify `python scripts/check-docs-voice.py` passes and every rule in the spec's "AI contribution policy" requirement appears in it. Done: sections follow RobotCode's policy; "In this repository" and "RobotCode first" carry the repository rules. The voice check passes.

## 2. Agent guide (D1–D3)

- [x] 2.1 Write `AGENTS.md` (at most about 120 lines) with these sections: Layout, Checks (one backticked command per bullet, copied from `ci.yml`), Generated files (each with its regenerate command), Never commit, OpenSpec workflow, RobotCode first (the rule plus the capability map, linking each guide page under https://robotcode.io/guides/cli/), and Policy (link). Verify every command in Checks runs locally on a clean checkout after `uv sync --all-extras`. Done: 85 lines. Each Checks command ran locally and passed (rf-core's suite has two environment-only failures, recorded in `repo-cleanup` 6.1). The harness suite and the security gate commands are listed outside Checks, because they run in other jobs and workflows.
- [x] 2.2 Add `CLAUDE.md` containing only `@AGENTS.md`; verify Claude Code shows the `AGENTS.md` content in `/memory` when started at the repository root. Done: a `claude -p` session (Haiku 5.5) at the worktree root, with every file tool disallowed, quoted the guide's first heading and the variants command.

## 3. Templates and OpenSpec (D5)

- [x] 3.1 Add an "AI assistance" section to `.github/pull_request_template.md` (disclosure, or "none") and the checklist item "Robot Framework capabilities go through `robotcode`; gaps are reported upstream"; add a disclosure note to `.github/ISSUE_TEMPLATE/plugin-feedback.yml`. Verify the issue form still renders: `python -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" .github/ISSUE_TEMPLATE/plugin-feedback.yml`. Done: the item sits in a new "Before you open it" list without a checkbox, because the template has no checkboxes since `lean-governance` (D7). The form parses.
- [x] 3.2 Add `context` and `rules` (proposal: name the `robotcode` command or say why none fits; tasks: every task has a verify clause) to `openspec/config.yaml`; verify `openspec instructions proposal --change ai-contributor-docs --json` returns them. Done: `openspec instructions proposal` returns the context with the RobotCode-first rule and the proposal rule; `instructions tasks` returns the verify rule.

## 4. Contributor docs (D6)

- [x] 4.1 In `CONTRIBUTING.md`, add the opening links to `AGENTS.md` and `AI_POLICY.md`, replace the review-group list with a link to `GOVERNANCE.md`, and fix the layout block (`legacy/`, `openspec/`, how `bundles/` is generated). Keep "Versions". Verify `python scripts/check-docs-voice.py` passes and `tests/test_repository_references.py` passes. Done: the Review section keeps the request to mention a plugin's `catalog.yaml` maintainers, which `lean-governance` relies on.
- [x] 4.2 Link `AGENTS.md` and `AI_POLICY.md` from `README.md` (contributing section); verify the docs voice check passes. Done.

## 5. Checks (D4)

- [x] 5.1 Add `tests/test_contributor_guidance.py` for the "Agent guide matches CI" and "PR template asks about AI use and RobotCode" requirements; verify it passes, and fails when (a) a `scripts/` path in `AGENTS.md` is renamed, (b) a Checks command is missing from `ci.yml`, (c) `CLAUDE.md` no longer imports `AGENTS.md`, (d) the RobotCode item is removed from the PR template (try each by temporary edit, then revert). Done: (a) and (b) are tests on a scratch copy; (c) and (d) failed the tests when tried by temporary edit and were reverted.
- [x] 5.2 Run `python -m pytest tests/ --ignore=tests/eval`, `python scripts/build-catalog.py --check`, `bash scripts/check-drift.sh` and `python scripts/check-docs-voice.py`; verify all pass. Done: all pass (858 shared tests).

## 6. PR

- [x] 6.1 Open a PR against `main` (ask before posting) with an AI-assistance disclosure in its description; verify the required checks pass. Done: #33, with the disclosure under "AI assistance", merged as `46067e0` with 25 checks passing.

## 7. Initial check

- [ ] 7.1 After merge, check the new policy and agent guide in use: one full CI run on `main`, one local run of the checks in `AGENTS.md` or CONTRIBUTING, and the next contributor PR. Write down anything that broke or got harder. If a decision in `design.md` turns out wrong or risky, propose the change to the maintainer and update `design.md`. Verify that the findings are recorded in this change.

  Findings so far (2026-11-17):
  - Local run of the `AGENTS.md` Checks list, command by command, on `46067e0`: every command exists and runs as written; `tests/test_contributor_guidance.py` passes. The only failure was the rf-core venv test, a test bug recorded in repo-cleanup 7.1 and fixed in the follow-up PR.
  - Harder than it should be: the Checks list gives no setup step. The commands need Robot Framework, the libraries and pytest installed. CONTRIBUTING has `uv sync`, but `AGENTS.md` doesn't point to it, so an agent that reads only `AGENTS.md` has to guess. Fixed in the follow-up PR, with the maintainer's agreement: a setup line before the list (`uv sync --all-packages`, `uv run rfbrowser init chromium`).
  - Still open: the next contributor PR, to see whether the "AI assistance" section and the RobotCode item get filled in. Tick this task once one has come in.
