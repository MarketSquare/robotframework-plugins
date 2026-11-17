## Why

RobotCode's CLI (https://robotcode.io/guides/cli/) is the base of the Robot Framework AI toolstack: it runs suites with the project's `robot.toml` and profiles, discovers tests, analyses code, reads results, browses keyword documentation, and offers a REPL and a terminal debugger. Our skills already tell agents to use it ("Keywords: `robotcode doc keyword`, not memory; results: `robotcode results`, not output.xml", `plugins/rf-core/scripts/maybe_inject_rf_context.mjs:62`), and the validation hooks call `robotcode analyze code`. The repository's own tooling does the opposite in several places:

- `scripts/check-skill-keywords.py` (617 lines) and the harness's `scoring/keyword_resolution.py` (344 lines) resolve keywords themselves with `robot.api.get_model` and `LibraryDocumentation`. The harness also needs committed libdoc spec files for AppiumLibrary and PlatynUI because it assumed they "cannot run on the CI runner". Both libraries install and load on Linux CI; `robotcode analyze code` resolves their keywords without a device or desktop.
- The grader runs plain `robot` and parses `output.xml` with ElementTree in four modules, where `robotcode robot` and `robotcode results --format json` give the same counts and failure messages.
- The deprecated-keyword check is a three-pattern regex.

Each re-implementation is code we maintain, that drifts from how Robot Framework and RobotCode behave, and that improves only this repository. Gaps we find should be fixed in RobotCode so every AI solution for Robot Framework gets them.

## What Changes

- **Keyword checks use `robotcode analyze code`.** `check-skill-keywords.py` writes the skills' Robot Framework snippets into a temporary project and runs `robotcode --format json analyze code` on it; it maps `KeywordNotFound`, `DeprecatedKeyword` and argument `DataError` diagnostics back to the Markdown file and line. What stays custom: Markdown extraction, the allowlist, the `Wait For Condition` vocabulary check, and close-match suggestions (from `robotcode doc keywords --format json`). Legacy `Run Keyword If`/`Unless` comes from Robocop's `DEPR08` rule, which the hooks already use.
- **The eval harness drops libdoc spec files.** `keywords_resolve` resolves through `robotcode analyze code` against the installed libraries; `min_calls` counting stays custom but takes library keyword names from `robotcode doc keywords --format json`. The `spec_dir`/`specs` task params and `eval/graders/specs/` (added by PR #20) are removed. `no_deprecated_keywords` uses the `DeprecatedKeyword` diagnostic plus Robocop's deprecation rules instead of its regex list.
- **The grader runs and reads through robotcode.** `robot_pass`, `robot_dryrun`, the rf-language and rf-python-library graders and `scripts/desktop-live-check.py` run `robotcode robot` and read `robotcode results summary/show --format json`; the ElementTree parsers are deleted.
- **The opt-in per-file dry-run hook runs `robotcode robot --dryrun`**, so `robot.toml` and profiles apply as in the other hook tiers.
- **A guard keeps it that way.** `scripts/check-robotcode-first.py` fails CI when tooling under `scripts/`, `src/`, `plugins/*/scripts`, `plugins/*/skills/*/scripts` or `plugins/*/hooks` uses a Robot Framework API or command that RobotCode covers (libdoc, result parsing, suite building, running `robot`/`rebot`/`libdoc` directly) outside an allowlist. Each allowlist entry names the file, the pattern and why RobotCode doesn't cover it; an entry that matches nothing fails.
- **Gaps go upstream.** The design lists the RobotCode gaps found (for example, failed library imports share the generic `DataError` code with argument errors). Each becomes a drafted robotcode issue that the maintainer reviews and files under robotcode's AI policy.

Not changed: `check_library.py` (rf-python-library) and `rf_conventions.py` (rf-language) stay. Their findings (library-author defects, project style conventions) are not RobotCode capabilities; they get allowlist entries with reasons.

## Capabilities

### New Capabilities

- `robotcode-first-tooling`: repository tooling uses the RobotCode CLI for core Robot Framework capabilities, an automated guard with a reasoned allowlist enforces it, and capability gaps are reported to RobotCode instead of worked around.

### Modified Capabilities

- `skill-content-verification`: the deterministic keyword checker resolves through `robotcode analyze code` and reports argument-count errors too.
- `skill-eval-harness`: grader runs and result reading go through `robotcode robot` and `robotcode results`; static keyword resolution uses the installed libraries, not libdoc spec files.
- `rf-validation-hooks`: the opt-in per-file dry run uses `robotcode robot --dryrun`.

## Impact

- **Code:** `scripts/check-skill-keywords.py`, `scripts/desktop-live-check.py`, new `scripts/check-robotcode-first.py` and `scripts/robotcode-first-allowlist.toml`; `src/rf_skill_eval/grader/robot_runner.py`, `scoring/deterministic.py`, `scoring/keyword_resolution.py`, `scoring/custom/language.py`, `scoring/custom/python_library.py`; `plugins/rf-core/scripts/validate_robot.mjs` (tier 3).
- **Eval data:** the five PlatynUI and Appium task YAMLs lose `spec_dir`/`specs`; `eval/graders/specs/` is deleted. Task hashes change, so a GLM re-baseline is needed (maintainer-dispatched).
- **CI:** a new step in `ci.yml` runs the guard; the keyword job needs `robotcode` (already in the dev group).
- **Order:** PR #20 (`fix/realistic-eval-tasks`) merges first. `fix-desktop-eval-turn-overhead` (its `min_calls` requirement still mentions "spec-covered libraries") is archived first or reconciled in this change. The `ai-contributor-docs` change states the rule; this change enforces it for tooling.
- **Users:** only the opt-in dry-run hook changes behaviour, and only for projects without robotcode, which is already a documented prerequisite (`robotcode-prerequisite`).
