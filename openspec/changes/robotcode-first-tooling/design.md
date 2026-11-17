## Context

See proposal.md (Why). What the change builds on, checked on robotcode 2.8.0 with Robot Framework 7.5.1 in the repository's `.venv` (Linux, no display):

- **The model to copy.** `plugins/rf-core/scripts/validate_robot.mjs` (tier 0) and `validate_robot_project.mjs` run `robotcode --format json analyze code` from the project root and classify diagnostics by `code`. Tier 1 runs Robocop and classifies by rule id (`DEPR08` = `Run Keyword If`/`Unless`). Only tier 3, the opt-in dry run, still starts `python -m robot --dryrun`.
- **`robotcode analyze code` covers keyword resolution.** On a suite importing String, Collections, AppiumLibrary 3.2.1 and PlatynUI.BareMetal 0.12.0.dev330:
  - valid calls of all four libraries (`Open Application`, `Pointer Click`, …) give no diagnostic, without a device or desktop;
  - `Convert To Uper Case` and `Not A Real Keyword` give `KeywordNotFound` (severity 1);
  - `Convert To Upper Case    a    b    c` gives `DataError` "expected 1 argument, got 3";
  - AppiumLibrary's `Element Should Be Visible` gives `DeprecatedKeyword` (severity 4, a hint);
  - `Run Keyword If` gives nothing; Robocop 8.2.10 `--select "DEPR*"` reports it;
  - a missing library gives `DataError` "Importing test library 'NoSuchLib' failed: ModuleNotFoundError …";
  - the JSON is `{"diagnostics": {file: [{range, message, severity, code, source}]}, "summary": {files, errors, warnings, infos, hints}}`; one file takes about 0.8 s.
- **`robotcode results` covers result reading.** `robotcode --format json results summary -o out/output.xml` gives `{"status", "counts": {"total", "passed", "failed", "skipped", "notRun"}, …}`; `results show` adds a `tests` list with `name`, `fullName`, `status`, `message`, `source`, `lineno`. The output path is given with `-o`, not as an argument.
- **`robotcode doc keywords <Lib>` with `--format json`** lists `name`, `args`, `doc`, `short_doc`, `tags`, `source`, `lineno` per keyword. There is no `deprecated` field; deprecation shows only in `doc` (`**DEPRECATED!!** …`).
- **Where the repo re-implements this today:**
  - keyword resolution: `scripts/check-skill-keywords.py` (`get_model`, `LibraryDocumentation`, own matching with embedded arguments), `src/rf_skill_eval/scoring/keyword_resolution.py` (the same against libdoc JSON specs);
  - result parsing: `grader/robot_runner.py` `_parse_output_xml`, used by `deterministic.py` and `scoring/custom/language.py`; `scoring/custom/python_library.py` `_statuses`; `scripts/desktop-live-check.py` `result_of`;
  - running: the same four files start `robot` or `python -m robot`; `language.py` starts pinned versions with `uvx --from robotframework==X robot` (task on `sut-rf71`);
  - deprecation: `deterministic.py` `_DEPRECATED_PATTERNS` (three regexes).
- **The spec fallback.** PR #20 moves the AppiumLibrary and PlatynUI libdoc specs to `eval/graders/specs/` and adds `spec_dir`. CI's eval jobs run `uv sync --all-packages`, which installs the dev group with both libraries and `robotcode[all]`, so the specs are no longer needed there.
- **What is custom value, not re-implementation:**
  - `check_library.py`: library-author defects (rejected or leaked keywords, listener exposure, `str` in unions, TEST-scope state, broad `except`). They need the library object in-process; `robotcode doc lib` gives only the listing.
  - `rf_conventions.py`: separator, naming, BDD, template and layout conventions, from the parser.
  - `scoring/custom/platynui.py`: PlatynUI-specific checks (unsafe expressions) on the parsed model.
  - `min_calls` counting: RobotCode has no call graph.

## Goals / Non-Goals

**Goals:**
- No tooling resolves keywords, parses results or starts `robot` itself where RobotCode does it.
- One guard, in CI, that needs no human judgement per PR: a reasoned allowlist decides.
- Every gap found becomes a drafted RobotCode issue.

**Non-Goals:**
- Changing what the skills teach users; they already teach RobotCode.
- Rewriting `check_library.py` or `rf_conventions.py`.
- Replacing Robocop: it is part of `robotcode[all]` and RobotCode uses it.
- Scanning `installer/` or `tests/`: the installer doesn't touch Robot Framework, and tests may build fixtures however they need.

## Decisions

### D1. Skill keyword checker: materialise the snippets, let RobotCode resolve

For each library skill, `check-skill-keywords.py` writes a temporary project:
- one `.robot` file per fenced block or example file, with a generated `*** Settings ***` importing the skill's target library and the standard libraries the checker allows today;
- a fragment without a section header becomes the body of a generated test case;
- the `*** Keywords ***` sections of the whole skill go into one `skill.resource` that every file imports, so a keyword defined in one block resolves in another, as today.

It runs `robotcode --format json analyze code` once on the directory, maps each diagnostic back through a line table to the source file and line, and keeps only `KeywordNotFound`, `DeprecatedKeyword` and argument `DataError`. An import failure of the target library marks the skill `skipped (library not installed)`. Close-match suggestions use `difflib` over the names from `robotcode doc keywords --format json`. `Run Keyword If`/`Unless` comes from `robocop check --select DEPR08` on the same files. The `Wait For Condition` vocabulary check and the allowlist stay as they are.

Before switching, a parity run compares the new checker with the old on the current skills and on the test fixtures. Differences are explained in the PR; new true findings (for example argument errors the old checker never saw) are fixed or allowlisted.

Alternative: keep the extractor and matcher and only take keyword names from `robotcode doc keywords --format json` instead of `LibraryDocumentation`. It removes the libdoc import but keeps our own matching (embedded arguments, normalisation) and gains no argument checks. Fallback if the parity run shows that materialised snippets give noise that can't be suppressed (for example duplicate keyword definitions across blocks).

### D2. `keywords_resolve`: analyse, then count

The check runs `robotcode --format json analyze code <suite>` in the workspace. An error diagnostic (`KeywordNotFound`, argument `DataError`, or an import failure of a library listed in `required_libraries`) fails it. For `min_calls`, the existing call-graph walk stays (allowlisted `get_model`), but a call counts as a library call when its name is in the keyword set of an imported non-standard library, read with `robotcode --format json doc keywords <Library>` and cached per library. The `specs` and `spec_dir` params, `_libdoc()` and `eval/graders/specs/` go; `validate-tasks` rejects the params.

Alternative: keep the specs as a fallback for libraries that don't install. Rejected: every library in the tasks installs on CI, and a fallback that never runs rots, as the spec path did.

### D3. Grader runs: one helper over `robotcode robot` and `robotcode results`

A single helper replaces `robot_runner.run_robot`, `_parse_output_xml` and `python_library._statuses`. It runs `robotcode robot --outputdir <dir> [--dryrun] [args] <path>` and then `robotcode --format json results show -o <dir>/output.xml`. It returns counts and per-test status and message. `robotcode` is found next to `sys.executable` first, then on PATH, as `_robot_binary()` does today.

For pinned Robot Framework versions (`language.py`, task on `sut-rf71`), the helper runs `uvx --from "robotcode[runner]==<harness version>" --with robotframework==X robotcode robot …`, and results are read with `robotcode results` from the harness environment. Checked on 2026-11-17 (task 2.2): robotcode 2.8.0's runner runs Robot Framework 7.1.1 and the `sut-rf71` suite passes (3 of 3, generator "Robot 7.1.1"), so no `uvx … robot` call or allowlist entry is needed.

The analysis cache: `robotcode analyze code` writes `.robotcode_cache/` into the analysed project. The grader sets `ROBOTCODE_CACHE_DIR` to a folder in the run's artifacts, so nothing is added to the agent's workspace.

### D4. `no_deprecated_keywords`

The check reads the `DeprecatedKeyword` diagnostics from the same `analyze code` call and runs Robocop's hard-deprecation rules (`DEPR03/04/07/08/09/10/11`, the set the hooks already use). The regex list goes. This can flag more than before: library-deprecated keywords, `[Return]`, `Force Tags`. That is intended and is one reason for the re-baseline.

### D5. The guard

`scripts/check-robotcode-first.py` scans `.py`, `.mjs` and `.js` files under the tooling paths with line regexes for the patterns in the spec. It skips comment lines. It matches imports and calls, not file names, so prose that mentions `output.xml` (the hint in `maybe_inject_rf_context.mjs`) is not a finding. `scripts/robotcode-first-allowlist.toml` holds `[[allow]] file, pattern, reason`, mirroring `skill-keywords-allowlist.toml`; an entry that matches nothing fails.

It runs as a step in `ci.yml`'s lint job and as `tests/test_robotcode_first.py`, so the check is automated and needs no reviewer.

Allowlist after this change (expected):

| File | Pattern | Reason |
|---|---|---|
| `plugins/rf-core/skills/rf-python-library/scripts/check_library.py` | `LibraryDocumentation` | library-author defect analysis needs the in-process library object |
| `plugins/rf-core/skills/rf-language/scripts/rf_conventions.py` | `get_model`, `ModelVisitor` | convention detection; RobotCode has none |
| `src/rf_skill_eval/scoring/keyword_resolution.py` | `get_model` | `min_calls` call-graph counting |
| `src/rf_skill_eval/scoring/custom/platynui.py` | `get_model` | PlatynUI-specific usage checks |
| `scripts/check-skill-keywords.py` | `get_model` | only if the D1 fallback is taken |
| `src/rf_skill_eval/scoring/custom/language.py` | `uvx … robot` | only if D3's pinned-version runner doesn't work |

Regexes over source can be fooled. The guard is a tripwire for honest contributors and agents, not a sandbox, so a reviewer of a PR that touches the allowlist sees why each exception exists.

### D6. Order with other work

1. PR #20 merges (it adds `eval/graders/specs/` and `spec_dir`, which D2 deletes).
2. `fix-desktop-eval-turn-overhead` is archived, so its `min_calls` requirement is in the main spec. This change then words "spec-covered libraries" as "imported non-standard libraries" in a follow-up delta, or the requirement is reworded during its archive.
3. If `repo-cleanup` lands first, `scripts/validate-marketplace.py` is gone; otherwise it gets a temporary allowlist entry.

## RobotCode gaps found (drafts to file after review)

Tested on robotcode 2.8.0 with Robot Framework 7.5.1. None blocks this change; each makes our code simpler once fixed.

1. **Import failures have no own diagnostic code.** A failed library import is reported as `DataError`, the same code as an argument-count error. Tools that must tell "the environment is missing a library" from "the code is wrong" have to parse the message text (`Importing test library '…' failed`). The hook (`validate_robot.mjs`) and D1/D2 all need this distinction. Proposal: a distinct code such as `ImportFailed` / `LibraryImportFailed`.
2. **`doc keywords --format json` has no `deprecated` flag.** Deprecation is only in the free-text `doc`, written differently per library (`*DEPRECATED*`, `**DEPRECATED!!**`). Proposal: a boolean `deprecated` (Robot Framework's `KeywordDoc.deprecated`) in the JSON.
3. **The `DeprecatedKeyword` message for AppiumLibrary reads "is deprecated: !!."** It comes from AppiumLibrary's `**DEPRECATED!!** Use Expect Element instead` doc. Check against plain `robot` first; if Robot Framework's own warning is equally garbled, report it to AppiumLibrary instead.
4. **`KeywordNotFound` has no suggestions.** Robot Framework's runtime error offers "Did you mean …"; the static diagnostic doesn't. Optional; we compute suggestions from `doc keywords` meanwhile.

`robotcode/issues#689` (reading libdoc spec files) is moot after D2: our need for spec files goes away. Whether to close it is the maintainer's call.

## Risks / Trade-offs

- [Materialised snippets produce noise, such as duplicate keywords across blocks or fragments that only make sense in prose] → Parity run before switching; D1 fallback keeps our matcher with RobotCode's keyword names.
- [The skill checker gets slower: one `analyze code` per skill plus `doc keywords` per library] → One directory run per skill (about 1 s per file measured; the analysis cache is off in a fresh temp dir). Acceptable for a CI job; measure in the parity run.
- [A RobotCode release changes JSON fields or codes] → The JSON fields used are pinned in tests with recorded output; `robotcode[all]` stays pinned to a range in the dev group.
- [More checks find more issues, so eval scores move] → Expected. The re-baseline after merge records them; the PR states which checks became stricter.
- [The guard's regexes miss an indirect use (an alias import, `subprocess` with a variable)] → Accepted: it's a tripwire, and AGENTS.md (from `ai-contributor-docs`) states the rule for humans and agents.

## Migration Plan

1. Land the guard first with an allowlist covering every current use, so CI is green and new uses are blocked from day one.
2. Replace the uses one area at a time (grader helper, `keywords_resolve`, skill checker, hook tier 3, desktop live check), deleting allowlist entries as they go; the stale-entry rule forces this.
3. Re-baseline GLM in CI after the eval-facing parts merge.

Rollback: each step is its own commit; reverting one restores its allowlist entries.

## Confirmed decisions (maintainer, 2026-11-16)

Each decision stands for now. After implementation, task 8.1 checks it. If that check, or anything found along the way, shows a problem or a risk, the decision can change again. In that case, update this design before going on.

- **Stricter checks:** argument-count errors from `analyze code` and the Robocop deprecation rules are wanted, even though they flag more than today and move eval scores.
- **Windows PC:** robotcode may be installed in the Windows desktop venv for `scripts/desktop-live-check.py` (task 5.2).

## Open Questions

- None open. The Windows question is settled above.
