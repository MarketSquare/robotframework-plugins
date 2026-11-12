## 1. Branch

- [x] 1.1 After PR #2 and PR #3 have merged, branch `change/fix-desktop-eval-turn-overhead` from `main`; verify `git log` shows both merges. Done: branched from 3756236, which merges #2 and contains #3 (73d1a74).

## 2. Fixture README (D5)

- [x] 2.1 Verify on a Windows desktop which attributes PlatynUI exposes for Calculator: done 2026-11-12 on German Windows 11 with PlatynUI 0.12.0.dev330. `@Id='CalculatorResults'`, `@Id='num1Button'` and `@Id='num2Button'` match; `@AutomationId`, `@Name='One'` and `Window[@Name='Calculator']` don't.
- [x] 2.2 Confirm `plusButton` and `equalButton` with `platynui-cli query` on the same machine: done 2026-11-12. `@Id='plusButton'` (Name "Plus"), `@Id='equalButton'` (Name "Gleich") and `@Id='num1Button'` (Name "Eins") each match one enabled Button, reported twice because an unanchored `//` query reaches it through both the desktop and the app tree. A cold Calculator start can take more than 4 s; queries made earlier return nothing, without an error.
- [ ] 2.3 Rewrite the element table in `eval/fixtures/sut-platynui/README.md` with the `@Id` locators and the localised-window note from D5; verify no `@AutomationId` and no button `@Name` remains (`grep`), and that the README and `rf-platynui` name the same attributes.

## 3. Grader: library calls through user keywords (D1)

- [ ] 3.1 Record keyword calls per owner (test, suite/test fixture, user keyword body) in `scoring/keyword_resolution.py`, and compute `counted_library_calls` by expanding user-keyword calls from tests and fixtures, memoised, with a cycle guard; `min_calls` compares against it. Verify with new tests in `tests/eval` for the four scenarios of "Static keyword resolution counts library calls through user keywords" in `specs/skill-eval-harness/spec.md`, plus an embedded-argument wrapper (`Press Digit ${digit}`).
- [ ] 3.2 Report call sites, library call sites and counted library calls in the check summary; verify a test asserts on the summary text.
- [ ] 3.3 Update the `keywords_resolve` row in `plugins/rf-core/evals/tasks/README.md` to say how `min_calls` counts; verify `scripts/check-docs-voice.py` passes.

## 4. Grader: PlatynUI locator check (D6, D7)

- [ ] 4.1 Add `custom.platynui:locators_ok` under `src/rf_skill_eval/scoring/custom/`, taking `target` and `name_to_id`; verify with tests for the four scenarios of "PlatynUI tasks check locators statically", plus `@native:AutomationId` accepted, an `[@Id=… or @Name=…]` predicate accepted, and an `@AutomationId` in a comment ignored.
- [ ] 4.2 Let `suggests_plugin_or_passes` take `checks: [...]` (all must pass) alongside `check`; verify a test for each form, and that the other plugins' partial tasks load and score unchanged.
- [ ] 4.3 Add the locator check to `narrow-platynui-calculator-01.yaml` (gating) and to the partial task's `checks` list; verify `rf-skill-eval doctor --tasks-dir plugins/rf-desktop/evals/tasks/narrow` passes and both tasks load.
- [ ] 4.4 Re-grade offline the 72 stored rf-desktop sessions of runs 42887127109, 42993062842 and 43167186288 with tasks 3 and 4 in place; verify the static verdicts match the Windows live results of 2026-11-12 (only the 5 suites that use `@Id` for the display pass `platynui_locators`), and the 7 `min_calls` false failures no longer fail on call count.

## 5. Hooks: formatting drift opt-in (D2)

- [ ] 5.1 In `validate_robot.mjs`, start the tier-2 formatter only when `RF_AGENTSKILLS_FORMAT_CHECK` is truthy; verify with `plugins/rf-core/tests/test_hook_scripts.py` cases for "enabled shows the diff" and "unset starts no formatter and shows no diff".
- [ ] 5.2 Document the flag in `plugins/rf-core/hooks/README.md` (tier table and env-flag table); verify the README lists it next to `RF_AGENTSKILLS_FILE_DRYRUN`.

## 6. Hooks: Stop reminder after a run (D3)

- [ ] 6.1 In `maybe_remind_robot_tests.mjs`, track the positions of the last `.robot`/`.resource` write and the last Robot Framework run command, and stay silent when the run comes later; change the first step's wording to "Run the affected tests where they can run". Verify with hook tests for the three scenarios in `specs/stop-hook-safety/spec.md`, and that the existing once-per-session and `stop_hook_active` tests still pass.

## 7. Generated copies

- [ ] 7.1 Regenerate `bundles/rf-agentskills/` and any other generated variants from the rf-core sources; verify `scripts/check-drift.sh` and the "Check generated variants and plugin layout" check pass locally.

## 8. Skill (D4)

- [ ] 8.1 Add the "Check a keyword" line with `robotcode doc keyword PlatynUI.BareMetal "<Keyword>"` and `robotcode doc keywords PlatynUI.BareMetal "<text>"` to the `Library Import` section of `plugins/rf-desktop/skills/rf-platynui/SKILL.md` and bump its minor version; verify `scripts/validate-skills.py` and `scripts/check-skill-keywords.py` pass.

## 9. Live check (D8)

- [ ] 9.1 Write `scripts/desktop-live-check.py` (collect, screen, run with a fresh Calculator, waiting until `CalculatorResults` answers a query rather than a fixed sleep, a 150 s limit, report per tier and arm); verify unit tests for the collection and the screening (an `OperatingSystem` import and an `Evaluate` call are skipped with a reason) run on Linux without PlatynUI.
- [ ] 9.2 Document it in `docs/` (where the rf-desktop eval docs live): Windows setup with uv and the pinned PlatynUI and platynui-cli versions, running it in the desktop session directly or over SSH through an `/it` scheduled task, and how to read the report; verify `scripts/check-docs-voice.py` passes.
- [ ] 9.3 Run it on the maintainer's Windows PC (`desktop-7800x3d`) against the artifacts of run 42993062842; verify it reproduces the 2026-11-12 results (skill example passes; all eval suites fail as written under the German display language).

## 10. Tests, versions, PR

- [ ] 10.1 Bump rf-core and rf-desktop plugin versions with `scripts/bump-version.sh`; verify `scripts/validate-marketplace.py` passes.
- [ ] 10.2 Run `uv run pytest tests/eval plugins/rf-core/tests`, `ruff check src tests/eval` and `scripts/check-governance.py`; verify all pass.
- [ ] 10.3 Open the PR against `main` (ask before posting); verify the required checks pass.

## 11. Re-baseline (D9)

- [ ] 11.1 Dispatch `skill-evaluation.yml -f provider=openrouter -f runs=6` on the PR branch and commit the candidate baselines for every plugin; verify the follow-up PR eval reports pass, not rebaseline-needed.
- [ ] 11.2 From the run's transcripts, report rf-desktop's per-arm pass rates, turns per session, `robocop format` runs and `robotcode doc` calls against run 42993062842; verify the report is in the PR description.
- [ ] 11.3 Run the live check (9.3) on the new run's artifacts; verify its per-arm pass rates are in the PR description next to the static ones.
- [ ] 11.4 Ask the maintainer to dispatch `provider=claude` for all plugins, and commit those candidate baselines; verify the Claude baselines in the PR carry the new harness version.

## 12. Upstream (separate from the PR)

- [ ] 12.1 Draft a robotcode issue for `robotcode doc keywords <libdoc .json>` failing with `AttributeError: 'ResourceFile' object has no attribute 'specversion'`, with a minimal reproduction and the AI-use disclosure; the maintainer reviews and posts it.
