# Robocop Settings for BDD Steps

- [What each setting does](#what-each-setting-does)
- [Rules that stay on](#rules-that-stay-on)
- [Where the settings go](#where-the-settings-go)
- [Merging into an existing configuration](#merging-into-an-existing-configuration)
- [Running Robocop](#running-robocop)

Robocop's defaults expect Title Case keyword names, so sentence-style steps get a naming finding on almost every line. `assets/robocop-bdd.toml` changes only what sentence-style steps need; all other rules stay on. Add it only when Step 0 chose sentence style. A project with Title Case steps keeps its configuration as it is. The settings were checked with Robocop 8.2.10 and 9.4.0.

## What each setting does

| Setting | Without it | With it | Versions |
|---|---|---|---|
| `wrong-case-in-keyword-name.convention=first_word_capitalized` (NAME02) | every step definition is flagged | a definition starts with a capital or an embedded argument; Title Case keywords still pass; a lower-case definition (`the ATM is broken`) is still flagged | 8.x and 9.x |
| `wrong-case-in-keyword-name.pattern='s` (NAME02) | `${holder}'s balance is …` is flagged, because `'s` is read as the first word | possessive steps pass | 8.x and 9.x |
| `wrong-case-in-keyword-call.convention=first_word_capitalized` (NAME18) | every call such as `Then the ATM dispenses 20 EUR` is flagged | the prefix provides the capital | 8.x and 9.x |
| `per-file-ignores = { "*_steps.resource" = ["VAR06"] }` | `VAR … scope=TEST` is flagged in steps resources | allowed there and only there | 8.x and 9.x |
| format: `extend-select = ["AlignTemplatedTestCases"]` | `robocop format` squeezes outline tables to single separators | outline rows align under the column labels | 8.x and 9.x |
| format: `AlignTemplatedTestCases.args_with_test=keep` (not in the asset) | 9.x moves each example's values to a line of their own | values stay on the line of the test name | 9.x only |
| format: `NormalizeSeparators.skip_keyword_call_pattern=^(Given\|When\|Then\|And\|But)\s` | `robocop format` collapses hand-aligned columns after a step | calls with a BDD prefix keep their alignment | 8.x and 9.x |

- `args_with_test=keep` is left out of the asset, because Robocop 8.x doesn't know it: with that line, `robocop format` stops with `InvalidParameterError: AlignTemplatedTestCases: Failed to import`. 8.x keeps the values on the test line anyway. On 9.x, add the line to the format `configure` list. `robocop check` isn't affected.
- `per-file-ignores` needs steps resources named `<domain>_steps.resource`. For a steps resource with another name, put `# robocop: off=VAR06` on the first line of that file (works on 8.x and 9.x), or add its pattern to the table.

## Rules that stay on

| Rule | Why it helps a BDD suite |
|---|---|
| DOC01, DOC02, DOC03 (missing keyword, test and suite documentation) | step documentation is the glossary, test documentation holds the rule, suite documentation holds the story |
| TAG05 (all tests share a tag) | a rule tag that every test shares belongs in `Test Tags` |
| VAR01 (empty variable value) | declare state with `${None}`, `@{EMPTY}` or `&{EMPTY}` |
| ARG01 (unused argument) | a step that ignores its embedded argument is a sentence that lies |
| DEPR05 (`Set Variable` instead of `VAR`) | state uses `VAR` |
| MISC04 (inconsistent assignment sign) | on 9.x, `VAR` counts as "no `=`", so write assignments without `=`: `${balance}    Get Balance    ${holder}` |

## Where the settings go

- Robocop reads `robocop.toml`, `robot.toml` and `pyproject.toml`. In `robot.toml` and `pyproject.toml` the sections are `[tool.robocop.lint]` and `[tool.robocop.format]`; in `robocop.toml` they are `[lint]` and `[format]`.
- Prefer the file that exists. Most robotcode projects have a `robot.toml`, which accepts the `[tool.robocop.*]` sections next to robotcode's own settings.
- The nearest configuration file wins, and Robocop doesn't merge files. A `robot.toml`, `pyproject.toml` or `robocop.toml` in a subfolder that has its own Robocop section hides the root settings for every file below it. A file without a Robocop section is skipped. Put the BDD settings into the file the project's suites actually use, and keep one Robocop configuration per project.

## Merging into an existing configuration

Never overwrite a project's Robocop configuration. Propose the merge and explain it:
1. `configure`: append the three NAME02 and NAME18 lines. If the project already sets a `convention` for these rules, say that `first_word_capitalized` still accepts its Title Case keywords and only adds sentence-style steps.
2. `per-file-ignores`: add the `"*_steps.resource" = ["VAR06"]` entry to the existing table.
3. `select`: if the project enables only some rules, add the NAME02 and NAME18 lines only when those rules are in the list.
4. `extends`: if the project extends a shared configuration, change the project file, not the shared one.
5. Format: add the `[tool.robocop.format]` lines only when the project runs `robocop format`, and `args_with_test=keep` only on Robocop 9.x.

## Running Robocop

```bash
robocop check --no-cache tests resources                              # exit code 0: no findings
robocop check --no-cache --select NAME02 --select NAME18 tests        # only the naming rules
robocop format --no-cache --check --diff tests                        # what the formatter would change
```

Repeat `--select` once per rule. A comma-separated value (`--select NAME02,NAME18`) selects nothing: Robocop 8.2.10 and 9.4.0 print "did not match with any rule name or id", then "No issues found.", and exit 0.

Run Robocop from the project's environment; `robotcode[all]` installs it.
