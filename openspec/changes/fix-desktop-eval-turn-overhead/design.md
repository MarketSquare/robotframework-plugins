## Context

See proposal.md (Why) for the measurements. The parts of the current code that shape the approach:

- `scoring/keyword_resolution.py` collects every keyword call into one flat list (`_Parsed.calls`), with no note of whether a call sits in a test, a fixture or a user keyword body. `library_calls` is the number of those call sites that resolve to a spec library. The archived design of strengthen-skill-eval-harness gives `min_calls` one purpose: "so an empty or BuiltIn-only suite cannot pass".
- `validate_robot.mjs` runs three tiers per written file. Tier 2 (formatting drift, `robocop format --check --diff`) is informational. Its siblings, the per-file dry run (`RF_AGENTSKILLS_FILE_DRYRUN`) and project validation at Stop (`RF_AGENTSKILLS_PROJECT_VALIDATION`), are already opt-in through environment flags.
- `maybe_remind_robot_tests.mjs` streams the transcript and fires once per session if any `file_path` ends in `.robot` or `.resource`. It doesn't look at what happened after the write.
- `bundles/rf-agentskills/` holds generated copies of the rf-core scripts and hooks, checked in CI ("Check generated variants and plugin layout").
- The partial task's gating check is `custom.partial_install:suggests_plugin_or_passes`, which takes one nested `check` and passes when the answer suggests the plugin or that check passes.
- A live run on Windows (2026-11-12, `C:\workspace\platynui-exp` on the maintainer's PC) showed what the static checks miss; see proposal.md (Why). PlatynUI's own attributes there were `@Id` (from UIA AutomationId), `@Name` (localised) and `@native:*` for the raw UIA properties.
- The eval's baseline arm stages no plugin and so runs no hooks; the skill arm runs rf-core's hooks with every plugin. Hook changes therefore move every plugin's skill arm.

## Goals / Non-Goals

**Goals:**
- Make the fixture's locators the ones that work on a real desktop, and make the static grader reject the ones that don't.
- Make the counted measure match what `min_calls` was meant to check, without making a BuiltIn-only suite pass.
- Remove hook output that leads the agent to work the task didn't ask for, while keeping it available to users who want it.
- Re-baseline once, after all parts land.

**Non-Goals:**
- Changing the task prompts (they'd change the task hashes, and the prompt's "make sure every keyword exists" is a fair user request).
- Giving the baseline arm hooks, or turning hooks off in evals: the skill arm should measure what users install.
- The UserPromptSubmit routing to `rf-language`: it caused a second skill load, but the false failures that went with it come from the grader, which this change fixes.
- The partial tier staging only rf-core: that is the partial-install test by design.
- Fixing the robotcode `.json` libdoc crash; that goes upstream.
- Making the live check part of CI.

## Decisions

### D1. Count library calls by expanding user keywords from tests and fixtures

The parser records calls per owner: each test, each suite/test fixture, and each user keyword body (a keyword's own `[Setup]`/`[Teardown]` belong to its body). The count starts from tests and suite/test fixtures. A library call adds 1. A user-keyword call adds that keyword's expanded count, computed once per keyword with memoisation, and a keyword on the current expansion stack adds 0. Name matching reuses the existing normalisation and embedded-argument patterns, so `Press Digit 1` resolves to `Press Digit ${digit}`. The summary keeps `calls` and `library_calls` (call sites) and adds `counted_library_calls`.

Alternatives:
- Lower `min_calls` to 3 on the desktop tasks: fixes one task's symptom, leaves rf-mobile's `min_calls: 4` with the same trap, and lets a suite with three direct calls pass where the task flow needs four.
- Count distinct library keywords: a wrapped calculator suite has 3 (`Bring To Front`, `Pointer Click`, `Get Attribute`), so it still fails.
- Count call sites including user-keyword calls: an empty wrapper keyword would count, which breaks the BuiltIn-only guarantee.

### D2. Formatting drift becomes opt-in (`RF_AGENTSKILLS_FORMAT_CHECK`)

When the flag isn't truthy, tier 2 doesn't start the formatter. The flag is parsed like the other `RF_AGENTSKILLS_*` booleans.

Alternatives:
- Reword the hint as optional: the agent acted on the hint in 19 of 36 sessions, and wording rarely stops a model from acting on a diff it has been shown.
- Show it at most once per session: it already fired about once per session; the cost is the follow-up, not repetition.
- Turn it off only in evals: the eval would no longer measure the installed behaviour.

Deprecation findings (tier 1) and errors (tier 0) stay on; they change correctness, not style.

### D3. The Stop reminder looks for a run after the last write

The transcript scan tracks two positions: the last tool call that wrote a `.robot`/`.resource` file (as today), and the last Bash command matching a Robot Framework run (`robot`, `python -m robot`, `robotcode robot`, any options). If the run comes after the write, the hook exits without output. The once-per-session marker and the `stop_hook_active` short-circuit are unchanged. The first step's wording becomes "Run the affected tests where they can run: …".

Alternative: detect "cannot run here" from the prompt. Too fragile, and the dry run the agent already did is the stronger signal.

### D4. The skill's lookup line moves up

A short "Check a keyword" line goes in `Library Import` (before `Core Keywords Quick Reference`), naming `robotcode doc keyword PlatynUI.BareMetal "<Keyword>"` and `robotcode doc keywords PlatynUI.BareMetal "<text>"`. The closing line stays. The skill's version gets a minor bump. Whether DeepSeek follows it is measured in the re-baseline run (`robotcode doc` calls per session, from the transcripts), not assumed.

### D5. The fixture README lists `@Id` locators, verified on Windows

Verified with `platynui-cli query` on Windows 11 (German): `@Id='CalculatorResults'`, `@Id='num1Button'` and `@Id='num2Button'` match; `@AutomationId='CalculatorResults'`, `@Name='One'` and `Window[@Name='Calculator']` don't. The README's table becomes:

| Element | XPath |
|---|---|
| Digit buttons | `//control:Button[@Id='num1Button']` … `[@Id='num9Button']` |
| Plus / Equals | `//control:Button[@Id='plusButton']`, `//control:Button[@Id='equalButton']` |
| Result display | `//control:Text[@Id='CalculatorResults']` (its `Name` holds the shown value, e.g. "Display is 3", localised) |
| Main window | `//control:Window[@Name='Calculator' or @Name='Rechner']`, noting that window names are localised |

`plusButton` and `equalButton` are confirmed during implementation with the same query. A short note under the table says that `@Name` values follow the display language and that PlatynUI exposes the UIA AutomationId as `@Id`, matching the skill. The skill needs no correction.

### D6. `platynui_locators` is a custom check driven by the task

A new `custom.platynui:locators_ok` check parses the suite like `keywords_resolve` (suite, resources, variable values) and scans every string argument and variable value for XPath attribute tests. It fails on `@AutomationId` not preceded by `native:`, and on `@Name='<value>'` where the task maps that value to an Id (`name_to_id: {One: num1Button, Two: num2Button, Plus: plusButton, Equals: equalButton}`), unless the same predicate also accepts an `@Id`, as in `[@Id='num1Button' or @Name='One']`. The mapping lives in the task YAML, so the check stays generic; the README is documentation, not grader input.

Alternatives:
- A regex over the raw file: simpler, but it would also flag comments and documentation (one suite explained `@Id` in a comment and then used `@AutomationId`).
- Reading the mapping from the README: couples the grader to a Markdown table.
- Only the `@AutomationId` rule: catches 49 of the 58 failures in the localised live pass, but not the `@Name='One'` suites, which fail on any non-English desktop.

### D7. The partial fallback takes a list of checks

`suggests_plugin_or_passes` accepts `checks: [...]` besides `check`; with a list, all must pass. The partial task uses `[keywords_resolve, platynui_locators]`. The single-`check` form keeps working for the other plugins' partial tasks.

### D8. The live check is a script run on the Windows machine

`scripts/desktop-live-check.py` runs on the Windows desktop, inside the project venv with PlatynUI installed. It takes a downloaded `skill-eval-full-rf-desktop-<run>` artifact directory. It:

1. collects `workspace/tests/*.robot` from the PlatynUI narrow and partial sessions, plus the skill's example;
2. screens each suite with `robot.api.get_model` (allowed imports, banned keywords), skipping unsafe ones with a reason;
3. for each suite, closes and starts Calculator, runs `robot` with a 150 s limit, and reads `output.xml`;
4. prints a table per tier and arm and the top failure messages.

The run must happen in the logged-in desktop session; the doc shows running it there directly, or over SSH through a scheduled task created with `schtasks /create … /it`, as was done for the measurements in proposal.md. It reports results only and never writes baselines.

Alternatives:
- A CI job on a self-hosted Windows runner: needs an always-on, unlocked desktop session and a registered runner; worth it later if the manual check proves useful.
- Running the suites with `--dryrun`: proves nothing about locators.

### D9. One branch, one re-baseline

The change branches from `main` after PR #2 (OpenRouter tier) and PR #3 (its baselines) have merged. All parts land in one PR, then one OpenRouter dispatch (`runs=6`) regenerates every plugin's OpenRouter baselines, and one `provider: claude` dispatch, started by the maintainer, regenerates the Claude ones. Both go in the same PR so the gate never compares the new grader or hooks against old baselines.

### D10. The CI eval model switches to GLM 5.3 Flash

The maintainer chose GLM 5.3 Flash for all CI evals (2026-11-13). The switch goes into this change, so no CI run uses DeepSeek again and the one re-baseline of D9 runs on GLM: `OPENROUTER_MODELS` holds only `z-ai/glm-5.3-flash`, the price table gets its list prices (input $0.0399, cache read $0.03, output $0.0784 per million; cache writes priced as input, since OpenRouter lists none), the workflow's `OPENROUTER_MODEL` changes, and baselines move to `baselines/openrouter/glm-5.3-flash/`. The DeepSeek baselines of run 43263363544 are removed; git keeps them. The turn factor stays 1.5 until GLM's turn-limit stops are known from the re-baseline.

## Risks / Trade-offs

- [D1 makes `min_calls` easier to meet: a wrapper called four times with one library call inside passes `min_calls: 4`] → `min_calls` is a floor against empty suites, not a coverage check; the tasks' `file_contains` checks still require the result check and the target window.
- [D2 removes formatting help users may have relied on] → Documented in the rf-core hook README and the release notes, with the flag to turn it back on.
- [D3 skips the reminder after a failing run] → Failing runs are reported by `report_pending_errors.mjs` and rf_error_hints, not by this reminder.
- [D4 may not change DeepSeek's behaviour] → Measured, not assumed; if it doesn't, the next step is a separate decision.
- [D6 only knows the attributes and names it is told about] → It targets the mistakes measured on a real desktop; the live check (D8) stays the way to find new ones.
- [D8 runs model-written suites on a maintainer's machine] → The screening step allows only PlatynUI and standard libraries and rejects `Evaluate`, process and file-system keywords; every suite in the measured runs passed that screen.
- [The live check depends on the display language] → It reports the language it ran under; the README and the locator check avoid `@Name` for controls, so suites that follow them pass under any language.
- [Re-baselining both tiers depends on the maintainer's Claude dispatch] → The PR stays open until both are in; the OpenRouter part can be verified first.

## Migration Plan

No data migration. Old baselines are replaced in the same PR. Rollback is a revert of the PR, which restores the old baselines with the old grader and hooks.

## Open Questions

- Whether `Pointer Click` should also count when called through `Run Keyword`-style BuiltIn keywords (`Run Keyword    Pointer Click    …`). No session in the analysed runs did this; the current code doesn't count it either.
