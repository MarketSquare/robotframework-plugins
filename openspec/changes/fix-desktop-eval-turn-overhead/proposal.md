## Why

On the OpenRouter tier (DeepSeek V4.1 Flash, N=6, runs 42887127109, 42993062842 and 43167186288), rf-desktop's skill arm scores below the baseline arm on the static gate: narrow 11/18 against 14/18, partial 14/18 against 17/18. Running the 63 suites those sessions wrote against real Windows Calculator (German Windows 11, PlatynUI 0.12.0.dev330, 2026-11-12) turns that around:

- **The `sut-platynui` fixture README gives locators that don't work.** PlatynUI exposes the UIA AutomationId as `@Id`, and plain `@AutomationId` matches nothing. `@Name` follows the display language (`Eins`, `Gleich`, `Rechner`). All 63 suites used the README's `@Name='Calculator'` window locator and failed as written. With the names translated, the only passing suites were the 5 that used `@Id` for the result display, all from the skill arm (narrow 5/16 against 0/14); every other failure was `@AutomationId='CalculatorResults'`. The skill's own example passed both times. The skill was right, and the README contradicted it.
- **The static gate can't see this.** `keywords_resolve` only checks that keywords exist, so it passed most of the suites that fail on a desktop.
- **It also fails correct suites.** 7 skill-arm sessions, and no baseline session, wrote a suite that wraps `Pointer Click` in a user keyword (the style `rf-platynui` and `rf-language` both teach) and failed with `library_calls=3`, below `min_calls: 4`. The check counts library call sites, not the calls a run makes.
- **rf-core hooks add turns the baseline arm never pays.**
  - After a formatting-drift hint, the model ran `robocop format` and re-checked in 19 of 36 sessions.
  - The Stop reminder to "run the affected tests" added 0–5 calls on a machine where nothing can run.
- **Both arms spend turns parsing the libdoc JSON.** Each session made 12–16 `python -c` calls on the 84 KB spec, often failing. No session used `robotcode doc keyword`, which the skill names only in its last line.

Raising rf-desktop's turn factor to 2.0 didn't help (the sessions used the extra turns and still hit the limit). The fix is to correct the fixture, make the grader see locator mistakes and stop it failing correct suites, and remove the turn overhead.

## What Changes

- **The `sut-platynui` README uses working locators:**
  - `@Id` for the buttons and the result display (`num1Button`, `num2Button`, `plusButton`, `equalButton`, `CalculatorResults`), as verified on Windows;
  - a window locator that doesn't depend on the display language.

  This is the main fix.
- **A new static check, `platynui_locators`, for the PlatynUI tasks.** It fails a suite whose XPath uses a plain `@AutomationId`, or that finds a Calculator control only by an English `@Name`. It is gating on the narrow task and part of the partial task's fallback check. The task YAMLs change, so their hashes change.
- **`keywords_resolve` counts library calls reached through user keywords.**
  - Each call of a user keyword adds the library calls in its body, recursively, with a cycle guard.
  - `min_calls` keeps its purpose: an empty or BuiltIn-only suite still fails.
  - The summary reports both the call sites and the counted calls.
- **The per-file validation hook's formatting-drift tier becomes opt-in** (`RF_AGENTSKILLS_FORMAT_CHECK=on`). Formatting is cosmetic, and the hint costs one to three turns per written file. **BREAKING (hook output):** sessions no longer see formatting diffs by default.
- **The Stop test reminder changes.**
  - It is skipped when the session already ran the suite (`robot`, `robotcode robot`, including `--dryrun`) after its last `.robot`/`.resource` write.
  - Its wording says to run the tests "where they can run".
- **`rf-platynui` points keyword checks to robotcode** (`robotcode doc keyword PlatynUI.BareMetal "<Keyword>"`) in its workflow, not only at the end of the file.
- **A documented, manual live check for rf-desktop.** It runs the eval sessions' PlatynUI suites, and the skill's example, on a Windows desktop and reports pass rates per arm. It is run before a release and whenever the fixture or the skill's locator guidance changes. It isn't part of CI.
- **All plugins are re-baselined on both tiers once, after these land together.**
  - The grader and task changes move the rf-desktop and rf-mobile results.
  - The hook changes move every skill arm.
- **Out of scope, tracked separately:** the robotcode crash on `robotcode doc keywords <libdoc .json path>` (`AttributeError: 'ResourceFile' object has no attribute 'specversion'`), to be reported upstream.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-eval-harness`:
  - adds a requirement for how `keywords_resolve` counts library calls;
  - adds the `platynui_locators` check for PlatynUI tasks;
  - adds a requirement for the manual live check of desktop suites.
- `rf-validation-hooks`: "Formatting drift check" becomes opt-in.
- `stop-hook-safety`: adds a requirement that the test reminder is skipped once the session has run the suite after its last write.
- `platynui-skill`: adds a requirement that the skill's workflow points keyword checks to `robotcode doc keyword`.

## Impact

- **Fixture and tasks:**
  - `eval/fixtures/sut-platynui/README.md`;
  - `plugins/rf-desktop/evals/tasks/narrow/narrow-platynui-calculator-01.yaml` and `.../partial/partial-platynui-calculator-01.yaml` (new check, new task hashes).
- **Code:**
  - `src/rf_skill_eval/scoring/keyword_resolution.py`, a new custom check under `src/rf_skill_eval/scoring/custom/`, and their tests;
  - `plugins/rf-core/scripts/validate_robot.mjs` and `maybe_remind_robot_tests.mjs` with their tests;
  - the rf-core hook README;
  - the generated copies under `bundles/`.
- **Content:**
  - `plugins/rf-desktop/skills/rf-platynui/SKILL.md` (minor version bump);
  - `plugins/rf-core/evals/tasks/README.md` (the `min_calls` wording);
  - a new section in `docs/` for the desktop live check, with the runner script under `scripts/`.
- **Baselines:** every plugin's OpenRouter and Claude baselines are regenerated. The Claude ones need a manual `provider: claude` dispatch on the maintainer's subscription.
- **Releases:** rf-core and rf-desktop get new plugin versions.
