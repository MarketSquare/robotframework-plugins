---
name: rf-run-digest
description: "Use after an RF run: read results with robotcode results, not output.xml."
license: Apache-2.0
compatibility: "Requires robotcode[all]>=2.8 (or robotcode[runner]) in the project environment for the results commands. No bundled scripts."
metadata:
  author: ai94iq
---

# Robot Framework Run Digest Skill

## When to use

Load this skill after a `robot` or `pabot` run, before you look at its result. output.xml and log.html are large; reading or parsing them wastes time and hides the few failures that matter.

## The rule

Read results with `robotcode results`, not output.xml. Never write your own output.xml parser.

## Read a run

Without `-o`, each command finds the result file from the project's robot.toml profile (output.xml or output.json). Pass `-o <file or directory>` after the subcommand to name another one. `--format json` goes before `results`.

```bash
uv run robotcode results summary                  # headline status and counts
uv run robotcode results summary --failed         # plus each failing test with its message
uv run robotcode results show --failed            # failing tests, one line each
uv run robotcode results stats --by suite --by tag # counts per suite and tag
uv run robotcode results log -bl "<longname>" --level FAIL   # keyword tree of one test
uv run robotcode results diff before.xml after.xml --only new-failures
```

Not using uv? Run the same commands with `.venv/bin/robotcode` or `poetry run robotcode`; see rf-setup.

Start with `summary --failed`. Open `log` for one named test only. Quote the summary counts and the failure messages when you report a run.

`--search TEXT` or `--search-regex PATTERN` narrows any command to tests whose names, messages, tags or log text match; `-i`/`-e` filter by tag and `-s`/`-t` by suite or test name. Filters run before counting, so `stats --by tag --search Timeout` counts only the matching tests.

`results` has no failure grouping. To group failures that differ only by ids or hosts, read `uv run robotcode --format json results summary --failed` and group the `failed[].message` values yourself. `results diff` always exits 0; read `newFailures` from its JSON to gate a build.

## Companion Skills

| Need | Skill |
|------|-------|
| Install Robot Framework or a library, fix the environment | `rf-setup` |
| Write tests, suites, user keywords, resources and variables in Robot Framework syntax | `rf-language` |
