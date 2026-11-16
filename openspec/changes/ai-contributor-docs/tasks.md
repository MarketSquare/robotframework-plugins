## 1. Policy (D1, D3)

- [ ] 1.1 Write `AI_POLICY.md`, following the sections of RobotCode's policy (human responsibility, disclosure, licensing and right to submit under Apache-2.0, issues and comments, pull requests, low-context submissions, enforcement), plus a section "In this repository" with the security, keyword, generated-file, eval-dispatch and realistic-eval rules, and the RobotCode-first rule; verify `python scripts/check-docs-voice.py` passes and every rule in the spec's "AI contribution policy" requirement appears in it.

## 2. Agent guide (D1–D3)

- [ ] 2.1 Write `AGENTS.md` (at most about 120 lines) with these sections: Layout, Checks (one backticked command per bullet, copied from `ci.yml`), Generated files (each with its regenerate command), Never commit, OpenSpec workflow, RobotCode first (the rule plus the capability map, linking each guide page under https://robotcode.io/guides/cli/), and Policy (link). Verify every command in Checks runs locally on a clean checkout after `uv sync --all-extras`.
- [ ] 2.2 Add `CLAUDE.md` containing only `@AGENTS.md`; verify Claude Code shows the `AGENTS.md` content in `/memory` when started at the repository root.

## 3. Templates and OpenSpec (D5)

- [ ] 3.1 Add an "AI assistance" section to `.github/pull_request_template.md` (disclosure, or "none") and the checklist item "Robot Framework capabilities go through `robotcode`; gaps are reported upstream"; add a disclosure note to `.github/ISSUE_TEMPLATE/plugin-feedback.yml`. Verify the issue form still renders: `python -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" .github/ISSUE_TEMPLATE/plugin-feedback.yml`.
- [ ] 3.2 Add `context` and `rules` (proposal: name the `robotcode` command or say why none fits; tasks: every task has a verify clause) to `openspec/config.yaml`; verify `openspec instructions proposal --change ai-contributor-docs --json` returns them.

## 4. Contributor docs (D6)

- [ ] 4.1 In `CONTRIBUTING.md`, add the opening links to `AGENTS.md` and `AI_POLICY.md`, replace the review-group list with a link to `GOVERNANCE.md`, and fix the layout block (`legacy/`, `openspec/`, how `bundles/` is generated). Keep "Versions". Verify `python scripts/check-docs-voice.py` passes and `tests/test_repository_references.py` passes.
- [ ] 4.2 Link `AGENTS.md` and `AI_POLICY.md` from `README.md` (contributing section); verify the docs voice check passes.

## 5. Checks (D4)

- [ ] 5.1 Add `tests/test_contributor_guidance.py` for the "Agent guide matches CI" and "PR template asks about AI use and RobotCode" requirements; verify it passes, and fails when (a) a `scripts/` path in `AGENTS.md` is renamed, (b) a Checks command is missing from `ci.yml`, (c) `CLAUDE.md` no longer imports `AGENTS.md`, (d) the RobotCode item is removed from the PR template (try each by temporary edit, then revert).
- [ ] 5.2 Run `python -m pytest tests/ --ignore=tests/eval`, `python scripts/build-catalog.py --check`, `bash scripts/check-drift.sh` and `python scripts/check-docs-voice.py`; verify all pass.

## 6. PR

- [ ] 6.1 Open a PR against `main` (ask before posting) with an AI-assistance disclosure in its description; verify the required checks pass.

## 7. Initial check

- [ ] 7.1 After merge, check the new policy and agent guide in use: one full CI run on `main`, one local run of the checks in `AGENTS.md` or CONTRIBUTING, and the next contributor PR. Write down anything that broke or got harder. If a decision in `design.md` turns out wrong or risky, propose the change to the maintainer and update `design.md`. Verify that the findings are recorded in this change.
