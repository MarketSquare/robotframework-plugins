## 1. Baselines before any change

- [ ] 1.1 Re-baseline the rf-core trigger sets (rf-language, rf-setup, rf-python-library) on train and validation under the default listing budget, before rf-bdd is staged. Store the results as the comparison baseline; verify that the files exist under `plugins/rf-core/evals/baselines/`.
- [x] 1.2 Verify the source skill's traps on the pinned tools: in a scratch project, run the 11 gotchas from spec `bdd-skill` against RF 7.4.2 / robotcode 2.8.0 / Robocop 8.2.10, and against RF 7.5.1 / Robocop 9.x. Record per trap the scratch suite, the versions and the outcome in a task note in this change folder.

## 2. Skill content

- [x] 2.1 Create `plugins/rf-core/skills/rf-bdd/` with `SKILL.md` frontmatter (`name: rf-bdd`, compact description ≤ 160 characters with a "Use" cue, `license`, `compatibility`, `metadata.author`, no `metadata.version`). Verify with `python scripts/validate-skills.py --channel all` and `python -m pytest tests/test_skill_descriptions.py`.
- [x] 2.2 Write the `SKILL.md` body in the spec skeleton: orientation with the `Verified against Robot Framework 7.4.2` line, `When to use` within 20 lines (naming rf-language with its signal and the robotcode skill), Version gate, Step 0 (conventions first, greenfield defaults), 11 house rules, the Write/Review/Gherkin-input modes, Gotchas (≥ 11), the reference table, Companion Skills. Port from `bdd-agentskill/skills/robotframework-bdd/SKILL.md` and cut the robotcode command table to the BDD uses. Verify ≤ 300 lines (≤ 500 hard).
- [x] 2.3 Port the seven references, applying D4: drop generic RF mechanics (keep a one-line rule naming `rf-language`), remove links between references, add contents lists to files over 100 lines, and state Robocop version differences in `robocop.md` (D6). Verify with `python scripts/check-docs-voice.py` and `python scripts/check-plugin-references.py`.
- [x] 2.4 Port `assets/robocop-bdd.toml` and the examples to `assets/examples/{sut,resource-strategy,world-strategy}/`, with relative `python-path` inside the tree, no symlinks and suite `Metadata` instead of test-level `[Metadata]`. Verify that both projects pass `robotcode analyze code`, `robot --dryrun` and a real run on RF 7.4.2 and 7.5.1, and that Robocop with the asset reports no NAME02/NAME18/VAR06 finding on 8.2.10 and 9.x.
- [x] 2.5 Run `python scripts/check_content_rules.py` and `scripts/security-scan.sh rf-core out/`. Add a reasoned baseline entry to `security/baselines/rf-core.yaml` only for confirmed false positives in the example Python files; verify that the gate passes.

## 3. Skill tests

- [x] 3.1 Write `plugins/rf-core/tests/test_bdd_skill.py`. The structure layer checks the frontmatter, the H2 order, the size budget, the reference set equal to the table, contents lists, no reference-to-reference links, no path into another skill, 11 house rules and ≥ 11 gotchas with the required terms. Verify with `python -m pytest plugins/rf-core/tests/test_bdd_skill.py`.
- [x] 3.2 Add the Robot Framework layer (skipped without `robot`): extract the `robotframework` blocks and `<!-- file: … -->` blocks from `SKILL.md` and the references, dry-run them against a copy of the examples (excluding `# Wrong` blocks), and dry-run and run both example projects for real. Verify that the tests pass locally with RF 7.4.2.
- [x] 3.3 Add the Robocop layer (installed Robocop, else `uvx --from "robotframework-robocop>=9.1,<10"`): the asset lints the examples cleanly, and the rule IDs cited in `robocop.md` exist. Verify that the tests pass.

## 4. rf-language and cross-references

- [x] 4.1 Edit rf-language: the `When to use` block names `rf-bdd` for BDD specifications; the casing gotcha says to follow the project's Robocop configuration instead of requiring Title Case BDD steps; `references/styles.md` and the BDD part of `references/embedded-arguments.md` get a one-line pointer to `rf-bdd`; the Companion Skills table gets the `bdd` row. Verify with `python -m pytest plugins/rf-core/tests/test_language_skill.py`.
- [x] 4.2 In `tests/test_skill_descriptions.py`: add catalogue key `bdd`, `REQUIRED_ROWS["rf-bdd"] = ("language", "setup", "python-library")`, `bdd` in rf-language's required rows, and rf-language ↔ rf-bdd in the sibling checks. Verify with `python -m pytest tests/test_skill_descriptions.py`; the listing total must stay ≤ `MAX_DESCRIPTION_TEXT`.
- [x] 4.3 Update `plugins/rf-core/scripts/maybe_inject_rf_context.mjs`: add `Given/When/Then specs -> rf-bdd;`, tighten the existing wording so the message stays ≤ 450 characters (D8), and add `rf-bdd` to the trigger identifiers. Add tests for the BDD skill-name trigger and for plain Cucumber/Java Gherkin not triggering. Verify with `python -m pytest plugins/rf-core/tests/test_hook_scripts.py`.
- [x] 4.4 Add a `rf-bdd` row to the routing table of `plugins/rf-core/agents/rf-test-architect.md` (BDD specifications, step vocabularies, Gherkin translation), keeping the body ≤ 120 lines. Run `python scripts/build-agent-variants.py`, then verify with `bash scripts/check-drift.sh` and `python -m pytest plugins/rf-core/tests/test_subagents.py plugins/rf-core/tests/test_agent_variants.py`.

## 5. Evals

- [x] 5.1 Create `eval/fixtures/sut-bdd-library/` from the source `library-base` (lending service with fixed dates, `robot.toml`), with overlays for the vocabulary task (`library-steps`) and the review task (`review-procedural`, 7 seeded issues). Add it to `eval/fixtures/README.md`. Verify that the fixture's own smoke suite passes with `robot`.
- [x] 5.2 Write `src/rf_skill_eval/scoring/custom/bdd.py` with `structure`, `living_docs` and `review_findings` (D10), plus unit tests under `tests/eval/`. Verify with `python -m pytest tests/eval -k bdd`.
- [x] 5.3 Write the five task YAMLs (`narrow-bdd-greenfield-01`, `narrow-bdd-outline-01`, `narrow-bdd-extend-vocabulary-01`, `narrow-bdd-review-01`, `adv-bdd-gherkin-row-01`), each with `skill: rf-bdd`, fixture `sut-bdd-library` and gating deterministic checks. Verify with `uv run rf-skill-eval doctor` and the task-loader tests.
- [x] 5.4 Write `plugins/rf-core/evals/triggers/rf-bdd.yaml`: ≥ 8 should-trigger and ≥ 8 should-not-trigger queries, both polarities in train and validation, negatives for rf-language syntax, Python library, results, Cucumber/Java, pytest-bdd and SpecFlow, and no skill ids in the queries. Verify with `python -m pytest tests/eval/test_trigger_sets.py tests/test_skill_descriptions.py`.
- [ ] 5.5 Tune rf-bdd's description on the train split (at most 5 iterations), then measure validation for rf-bdd and the rf-core siblings under the default budget. Verify the acceptance rule: rf-bdd recall ≥ 0.80 and should-not accuracy ≥ 0.90 (or rule (b) recorded), and no sibling below its 1.1 baseline. Run holdout and the 40000-character condition once each and report them.
- [ ] 5.6 Run the five tasks on the CI model, with and without rf-bdd installed. Store the baselines under `plugins/rf-core/evals/baselines/`, and verify that the eval gate passes with the new baselines.

## 6. Version, catalogue and docs

- [x] 6.1 Bump no version (D11). Run `python scripts/build-catalog.py`, then verify with `python scripts/build-catalog.py --check`, and that `rf-bdd` has no `metadata.version`.
- [x] 6.2 Add the change under `## Unreleased` in `CHANGELOG.md`, rf-core group (new `rf-bdd`, rf-language casing gotcha, hook and subagent routing); update `plugins/rf-core/README.md` (skill list) and the repository README's "Which plugins" row for `rf-core`. Verify with `python scripts/check-docs-voice.py`.
- [x] 6.3 Check the Claude Desktop and standalone export: `python scripts/build-skill-zips.py --out dist/skill-zips` and `python scripts/export-skills.py`. Verify that `rf-bdd` is exported with its assets and has no `${CLAUDE_SKILL_DIR}` left in plain copies.

## 7. Final verification and PR

- [x] 7.1 Run every CI check from CONTRIBUTING.md locally: `build-catalog.py --check`, `check-governance.py`, `check_content_rules.py`, `validate-skills.py --channel all`, `check-plugin-references.py`, `check-drift.sh`, `check-docs-voice.py`, `pytest tests/ --ignore=tests/eval` and `pytest plugins/rf-core/tests`. Verify that all of them pass.
- [x] 7.2 Try it in a live session: `claude --plugin-dir ./plugins/rf-core` in a fresh copy of `sut-bdd-library`, with the prompt "Write BDD acceptance tests for returning a book late". Verify that rf-bdd and rf-language load, the suite passes, and no `.feature` file is created. Done on 2026-11-19 with Claude Code and Haiku 5.5 in fresh copies of `sut-bdd-library/base`. The renewal prompt doesn't fit the fixture: the lending service has no renewal, and the agent (correctly) wrote failing tests and refused to invent the feature. With the late-return prompt, two runs: rf-bdd loaded in both, rf-language in one of them; the suites passed (5/5 and 10/10); no `.feature` file.
- [ ] 7.3 Commit on a branch from the current `main` and open a PR against `main` with the PR-template checklist filled in. Request a Foundation reviewer (verified plugin) and a security reviewer (hook script change).
