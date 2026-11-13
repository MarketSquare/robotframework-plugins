## 1. Schema and check (D1, D2)

- [x] 1.1 Add `skills` (array of unique kebab-case strings, `minItems: 1`) to `libraries.items.properties` in `schemas/catalog.schema.json`; verify tests in `tests/test_catalog.py` for "Skills per library accepted" and "Other unknown keys still rejected" (`skill:` singular), and an empty list rejected.
- [x] 1.2 Add `library_skill_problems()` to `scripts/build-catalog.py` and run it with the other checks; verify a test for "Missing skill reported" (message names the plugin, the library and the skill) and one for a removed plugin's manifest with a stale skill.

## 2. Data and generated catalogue (D3)

- [x] 2.1 Add `skills` to the libraries of rf-web, rf-api, rf-mobile and rf-desktop, as listed in the proposal; verify `scripts/build-catalog.py --check` passes after regenerating.
- [x] 2.2 Show the skills in `docs/catalog.md` (`Browser (robotframework-browser >=20,<21): rf-browser`) and regenerate; verify a test on the generated text and that `--check` fails when the committed `docs/catalog.md` is stale.
- [x] 2.3 Add a repository test that every library of every active technology plugin names its skills, and that together they cover all of the plugin's skills; verify it passes.

## 3. Installer (D4)

- [x] 3.1 Rebuild the bundle and add tests for "Passed through to tools" (`bundle.catalog()` from the dev bundle) and for a `fetch()` snapshot whose fake archive has `skills` in a manifest, plus "Absent field keeps working" (no `skills` key appears); verify `pytest tests/installer` passes.
- [x] 3.2 List `skills` in the README "Python API" table (absent means every skill of the plugin covers the library) and add a line to the 2026.11.0 changelog entry; verify `scripts/check-docs-voice.py installer/README.md installer/CHANGELOG.md` passes.

## 4. Docs, checks, PR

- [x] 4.1 Explain the field in CONTRIBUTING.md's `catalog.yaml` step, including that it must change when a skill is added or renamed; verify `scripts/check-docs-voice.py` passes.
- [x] 4.2 Run `pytest tests --ignore=tests/eval`, `scripts/build-catalog.py --check` and `scripts/check-drift.sh`; verify all pass. Done: `tests` 832 passed; `build-catalog.py --check`, `check-drift.sh` and `check-template.sh` pass, except `test_check_rf_environment_uses_project_venv`, which fails locally on a clean `main` too and passes in CI.
- [ ] 4.3 Open a PR against `main` that closes #7 (ask before posting); verify the required checks pass.
