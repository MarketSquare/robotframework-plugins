## 1. Branch

- [x] 1.1 After PR #2 and PR #3 have merged, branch `change/fix-desktop-eval-turn-overhead` from `main`; verify `git log` shows both merges. Done: branched from 3756236, which merges #2 and contains #3 (73d1a74).

## 2. Fixture README (D5)

- [x] 2.1 Verify on a Windows desktop which attributes PlatynUI exposes for Calculator: done 2026-11-12 on German Windows 11 with PlatynUI 0.12.0.dev330. `@Id='CalculatorResults'`, `@Id='num1Button'` and `@Id='num2Button'` match; `@AutomationId`, `@Name='One'` and `Window[@Name='Calculator']` don't.
- [x] 2.2 Confirm `plusButton` and `equalButton` with `platynui-cli query` on the same machine: done 2026-11-12. `@Id='plusButton'` (Name "Plus"), `@Id='equalButton'` (Name "Gleich") and `@Id='num1Button'` (Name "Eins") each match one enabled Button, reported twice because an unanchored `//` query reaches it through both the desktop and the app tree. A cold Calculator start can take more than 4 s; queries made earlier return nothing, without an error.
- [x] 2.3 Rewrite the element table in `eval/fixtures/sut-platynui/README.md` with the `@Id` locators and the localised-window note from D5; verify no `@AutomationId` and no button `@Name` remains (`grep`), and that the README and `rf-platynui` name the same attributes.

## 3. Grader: library calls through user keywords (D1)

- [x] 3.1 Record keyword calls per owner (test, suite/test fixture, user keyword body) in `scoring/keyword_resolution.py`, and compute `counted_library_calls` by expanding user-keyword calls from tests and fixtures, memoised, with a cycle guard; `min_calls` compares against it. Verify with new tests in `tests/eval` for the four scenarios of "Static keyword resolution counts library calls through user keywords" in `specs/skill-eval-harness/spec.md`, plus an embedded-argument wrapper (`Press Digit ${digit}`).
- [x] 3.2 Report call sites, library call sites and counted library calls in the check summary; verify a test asserts on the summary text.
- [x] 3.3 Update the `keywords_resolve` row in `plugins/rf-core/evals/tasks/README.md` to say how `min_calls` counts; verify `scripts/check-docs-voice.py` passes.

## 4. Grader: PlatynUI locator check (D6, D7)

- [x] 4.1 Add `custom.platynui:locators_ok` under `src/rf_skill_eval/scoring/custom/`, taking `target` and `name_to_id`; verify with tests for the four scenarios of "PlatynUI tasks check locators statically", plus `@native:AutomationId` accepted, an `[@Id=… or @Name=…]` predicate accepted, and an `@AutomationId` in a comment ignored.
- [x] 4.2 Let `suggests_plugin_or_passes` take `checks: [...]` (all must pass) alongside `check`; verify a test for each form, and that the other plugins' partial tasks load and score unchanged.
- [x] 4.3 Add the locator check to `narrow-platynui-calculator-01.yaml` (gating) and to the partial task's `checks` list; verify `rf-skill-eval doctor --tasks-dir plugins/rf-desktop/evals/tasks/narrow` passes and both tasks load. Done: both tasks load and `doctor` passes. The golden suite `tests/eval/golden/narrow-platynui-calculator-01/tests/calculator.robot` used the old README locators and failed the new check; it now uses `@Id`.
- [x] 4.4 Re-grade offline the 72 stored rf-desktop sessions of runs 42887127109, 42993062842 and 43167186288 with tasks 3 and 4 in place; verify the static verdicts agree with the Windows live results of 2026-11-12 (no suite that fails live passes `platynui_locators`), and the 7 `min_calls` false failures no longer fail on call count. Done: 63 sessions wrote a suite. The 7 false failures now pass `keywords_resolve` (counted 5–6 library calls), all in the skill arm: narrow skill arm 11/18 → 16/18, partial skill arm 14/18 → 16/18; baseline arms unchanged. `platynui_locators` passes 1 suite (narrow skill arm, `@Id` throughout), which also passed live. The other 4 live passes used `@Id` only for the display and English `@Name` for the buttons; they passed only after the names were translated, so the check rejects them, as the "Language-bound name rejected" scenario requires. No suite that failed live passes the check.

## 5. Hooks: formatting drift opt-in (D2)

- [x] 5.1 In `validate_robot.mjs`, start the tier-2 formatter only when `RF_AGENTSKILLS_FORMAT_CHECK` is truthy; verify with `plugins/rf-core/tests/test_hook_scripts.py` cases for "enabled shows the diff" and "unset starts no formatter and shows no diff".
- [x] 5.2 Document the flag in `plugins/rf-core/hooks/README.md` (tier table and env-flag table); verify the README lists it next to `RF_AGENTSKILLS_FILE_DRYRUN`.

## 6. Hooks: Stop reminder after a run (D3)

- [x] 6.1 In `maybe_remind_robot_tests.mjs`, track the positions of the last `.robot`/`.resource` write and the last Robot Framework run command, and stay silent when the run comes later; change the first step's wording to "Run the affected tests where they can run". Verify with hook tests for the three scenarios in `specs/stop-hook-safety/spec.md`, and that the existing once-per-session and `stop_hook_active` tests still pass.

## 7. Generated copies

- [x] 7.1 Regenerate `bundles/rf-agentskills/` and any other generated variants from the rf-core sources; verify `scripts/check-drift.sh` and the "Check generated variants and plugin layout" check pass locally.

## 8. Skill (D4)

- [x] 8.1 Add the "Check a keyword" line with `robotcode doc keyword PlatynUI.BareMetal "<Keyword>"` and `robotcode doc keywords PlatynUI.BareMetal "<text>"` to the `Library Import` section of `plugins/rf-desktop/skills/rf-platynui/SKILL.md` and bump its minor version; verify `scripts/validate-skills.py` and `scripts/check-skill-keywords.py` pass. Done: no version bump, since 1.0.0 is unreleased (see 10.1); the change is in the rf-desktop 1.0.0 CHANGELOG entry.

## 9. Live check (D8)

- [x] 9.1 Write `scripts/desktop-live-check.py` (collect, screen, run with a fresh Calculator, waiting until `CalculatorResults` answers a query rather than a fixed sleep, a 150 s limit, report per tier and arm); verify unit tests for the collection and the screening (an `OperatingSystem` import and an `Evaluate` call are skipped with a reason) run on Linux without PlatynUI.
- [x] 9.2 Document it in `docs/` (where the rf-desktop eval docs live): Windows setup with uv and the pinned PlatynUI and platynui-cli versions, running it in the desktop session directly or over SSH through an `/it` scheduled task, and how to read the report; verify `scripts/check-docs-voice.py` passes.
- [x] 9.3 Run it on the maintainer's Windows PC (`desktop-7800x3d`) against the artifacts of run 42993062842; verify it reproduces the 2026-11-12 results (skill example passes; all eval suites fail as written under the German display language). Done 2026-11-12 (German display language): the skill example passes; all 20 suites fail as written, 19 on `//control:Window[@Name='Calculator']` not found and 1 on its own window check. None skipped by screening. The first attempt reported every suite as "Calculator not ready"; the readiness check now compares raw bytes and names the last query output when it gives up.

## 10. Tests, versions, PR

- [x] 10.1 Record the rf-core and rf-desktop changes for release; verify `scripts/validate-marketplace.py` passes. Done: neither plugin has a release tag, so 1.0.0 is still unreleased; the changes go into the 1.0.0 (unreleased) CHANGELOG entries instead of a 1.1.0 bump, and `rf-platynui` stays at the plugin's 1.0.0 (validate-skills requires the two to match).
- [x] 10.2 Run `uv run pytest tests/eval plugins/rf-core/tests`, `ruff check src tests/eval` and `scripts/check-governance.py`; verify all pass. Done: `tests`, `plugins/rf-core/tests` and `plugins/rf-desktop/tests` pass, ruff and governance pass. `test_check_rf_environment_uses_project_venv` fails locally on a clean `main` checkout too (it passes in CI), so it isn't caused by this change.
- [ ] 10.3 Open the PR against `main` (ask before posting); verify the required checks pass.

## 11. Re-baseline (D9)

- [x] 11.1 Dispatch `skill-evaluation.yml -f provider=openrouter -f runs=6` on the PR branch and commit the candidate baselines for every plugin; verify the follow-up PR eval reports pass, not rebaseline-needed. Done: run 43263363544 (all five plugins, both arms, N=6) succeeded; its candidate baselines replace every plugin's OpenRouter baselines. The follow-up PR eval runs on the push.
- [ ] 11.2 From the run's transcripts, report rf-desktop's per-arm pass rates, turns per session, `robocop format` runs and `robotcode doc` calls against run 42993062842; verify the report is in the PR description.
- [ ] 11.3 Run the live check (9.3) on the new run's artifacts; verify its per-arm pass rates are in the PR description next to the static ones.
- [ ] 11.4 Ask the maintainer to dispatch `provider=claude` for all plugins, and commit those candidate baselines; verify the Claude baselines in the PR carry the new harness version.

## 13. CI eval model: GLM 5.3 Flash (D10)

- [x] 13.1 Switch `OPENROUTER_MODELS`, the price table, the workflow's `OPENROUTER_MODEL`, tests and docs (usage, local testing, ADR-005) to `z-ai/glm-5.3-flash`; verify `uv run pytest tests/eval` passes and no DeepSeek id is left outside history and archived changes. Done: 654 tests pass.
- [x] 13.2 After OpenRouter credits are topped up, dispatch `skill-evaluation.yml -f provider=openrouter -f runs=6` on this branch (GLM); commit the candidate baselines under `baselines/openrouter/glm-5.3-flash/` and remove `baselines/openrouter/deepseek-v4.1-flash/`. Verify the follow-up PR eval passes. Done: run 43397156347 (GLM, all plugins, both arms, N=6) succeeded for $5.86 of key spend (the DeepSeek re-baseline cost $10.14); its baselines are under `baselines/openrouter/glm-5.3-flash/`, and the DeepSeek folders are removed.
- [ ] 13.3 Repeat the rf-desktop report (11.2) and the live check (11.3) on the GLM run; verify both tables are in the PR description.

## 12. Upstream (separate from the PR)

- [x] 12.1 Draft a robotcode issue for `robotcode doc keywords <libdoc .json>` failing with `AttributeError: 'ResourceFile' object has no attribute 'specversion'`, with a minimal reproduction and the AI-use disclosure; the maintainer reviews and posts it. Done: drafted as an enhancement, not a bug, because `robotcode doc --help` names only libraries, resources and suites as TARGET. It reproduces on 2.8.0 and 2.9.0.dev186; an XML `.libspec` fails too, and no existing issue covers it. Posted after review as robotcodedev/robotcode#689.
