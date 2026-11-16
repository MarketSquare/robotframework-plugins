## 1. Root config and dependencies (D4)

- [ ] 1.1 Delete `.mcp.json`. Verify: `grep -rn "claude-flow" --exclude-dir=openspec --exclude-dir=.git .` finds only `.gitignore` (whose `.claude-flow/` and `.swarm/` lines stay, since they keep local tool files out).
- [ ] 1.2 Edit `pyproject.toml`:
  - remove `scipy`, `numpy`, `httpx`, `polars` and their mypy overrides;
  - remove the `validation` extra and the sdist `exclude` list;
  - remove `skills` from the ruff excludes, and rewrite the `tests/test_*.py` comment;
  - remove `pytest-asyncio` and `asyncio_mode` here and in `installer/pyproject.toml`;
  - fix the classifier comment that says the harness grades "rf-agentskills".

  Run `uv lock`. Verify: the `uv.lock` diff only removes packages; `uv sync --all-packages` succeeds; `uv run pytest -q` (tests/eval) passes; `uv run ruff check src tests/eval` and `uv run mypy` pass.

## 2. Eval harness dead code (D3)

- [ ] 2.1 Delete:
  - `domain/events.py`, `domain/skill.py` and `infrastructure/persistence/parquet_writer.py`;
  - `ConfigError`, `PersistenceError` and `VERDICT_STATUSES`;
  - `Settings.claude_model_default` and `Settings.rf_skill_eval_log_level`.

  Verify: `grep -rn "RunStarted\|parquet_writer\|ConfigError\|PersistenceError\|VERDICT_STATUSES\|claude_model_default" src tests scripts .github` finds nothing; `uv run mypy` and `uv run pytest -q` pass.
- [ ] 2.2 Remove the plugin MCP merge:
  - in `claude_code_runner.py`: `_extra_mcp_servers`, its use in `_mcp_servers`, and the plugin-server leak check;
  - its test in `tests/eval/test_runner_workspace.py`;
  - the `rf-tools` wording in `infrastructure/mcp/config_builder.py`.

  Verify: `uv run pytest -q tests/eval/test_runner_workspace.py tests/eval/test_providers.py` passes, and a dry-run batch (`uv run rf-skill-eval run --help` plus the existing runner tests) still writes the per-task `rf-mcp` server.
- [ ] 2.3 Remove `CLAUDE_MODEL_DEFAULT` from `.env.example` and `docs/ci/usage.md` (keep `RF_SKILL_EVAL_LOG_LEVEL`). Verify: `grep -rn CLAUDE_MODEL_DEFAULT --exclude-dir=openspec .` finds nothing.

## 3. CI and release (D5, D6)

- [ ] 3.1 Delete `.github/workflows/update-latest.yml` and `.github/actions/setup-eval/`. Verify: `grep -rn "setup-eval\|update-latest" .github scripts tests README.md RELEASING.md CONTRIBUTING.md` finds nothing.
- [ ] 3.2 Add a "no plugin MCP server" section to `scripts/check-drift.sh`: no `plugins/*/.mcp.json`, `plugins/*/servers`, or the same under `bundles/*`. Add a test in `tests/test_drift_detection.py` that creates `plugins/x/.mcp.json` in a temporary copy and expects drift. Verify: `bash scripts/check-drift.sh` passes on the tree, and the new test passes.
- [ ] 3.3 In `ci.yml`:
  - remove the variants and `validate-skills.py` steps from `validate-plugin`;
  - remove the `build-claude-plugin` job;
  - remove the Codex and Copilot steps and uploads from `build-portable-skills`;
  - remove `pytest-asyncio` from the `pip install` lines and their comments.

  Verify: on the PR, the required checks have the same names and pass, and `grep -n "rf-agentskills-claude-plugin\|codex/skills\|github/skills" .github/workflows/ci.yml` finds nothing.
- [ ] 3.4 In `release.yml`, pass `--skills skills` to `build-skill-zips.py`. Verify: locally, `python scripts/export-skills.py rf-web skills && python scripts/build-skill-zips.py --plugin rf-web --skills skills --out <tmp>` writes `rf-browser.zip` and `rf-selenium.zip` (no test covers this script today), and the `build-portable-skills` CI job, which runs the same pair, passes on the PR.

## 4. Scripts (D2)

- [ ] 4.1 Delete `scripts/validate-marketplace.py`, `scripts/docker-test-harness.sh`, `docs/installer/docker.md` and `docs/installer/docker/`. Verify: `grep -rn "validate-marketplace\|docker-test-harness\|installer/docker" --exclude-dir=openspec --exclude-dir=archive .` finds only `installer/CHANGELOG.md` history.
- [ ] 4.2 Fix the old names:
  - the `build-skill-zips.py` docstring (`robotframework-plugins install`, a real plugin in the usage example);
  - the `build-description-variant.py` docstring (it stages `plugins/`, not `skills/`);
  - the header of `scripts/templates/opencode-plugin.js`.

  Run `python scripts/build-agent-variants.py`. Verify: `python scripts/build-agent-variants.py --check` and `bash scripts/check-drift.sh` pass.

## 5. Docs (D1)

- [ ] 5.1 `git mv` the files listed in D1 to `docs/archive/`, and write `docs/archive/README.md` (one line each: date, what it was, what replaced it). Verify: `ls docs` shows only `archive/`, `catalog.md`, `ci/` and `installer/` if anything remains there.
- [ ] 5.2 Exclude `docs/archive/` in `scripts/check-docs-voice.py`. In `tests/test_repository_references.py`, replace the `docs/` prefix with `docs/archive/` and `docs/ci/architecture/adr/`. Add the ADR-006 status line. Verify: `python scripts/check-docs-voice.py` and `pytest tests/test_repository_references.py tests/test_docs_voice.py` pass.
- [ ] 5.3 Repoint links to moved files:
  - in the installer sources, tests and `pyproject.toml`;
  - in `plugins/rf-core/hooks/README.md`, `eval/fixtures/README.md` and `plugins/rf-core/evals/tasks/README.md`;
  - in the ADRs, and in `docs/ci/usage.md` (`ddd-design.md`).

  Run `python scripts/build-catalog.py` to refresh the bundle copy of the hooks README. Verify: a link check (`grep -rnoE "docs/[A-Za-z0-9_./-]+\.(md|txt)"` over the tree, each target exists) finds no dead link, and `python scripts/build-catalog.py --check` passes.
- [ ] 5.4 Fix the factual errors in current docs:
  - `docs/ci/usage.md:289,338`, `docs/ci/local-testing.md:25-30,267` and `docs/ci/faq.md:322-336` (the dead `skills/README.md` link);
  - `plugins/rf-core/hooks/README.md:381` (`plugins/rf-core/tests/test_hook_scripts.py`);
  - the docstrings of `tests/test_library_skill_structure.py:4-7` and `tests/_shell.py:34`;
  - the README "Prerequisites" line that calls the plugins "rf-agentskills".

  Verify: `grep -rn "sync-skills\|plugins/rf-agentskills/tests\|skills/README.md" README.md docs/ci plugins tests --include=*.md --include=*.py` finds only the drift test's assertion that `sync-skills.sh` doesn't exist; `python scripts/check-docs-voice.py` passes.

## 6. Specs and checks

- [ ] 6.1 Run the full local checks:
  - `uv run pytest -q`;
  - `python -m pytest tests --ignore=tests/eval`;
  - `python -m pytest plugins/rf-core/tests plugins/rf-desktop/tests`;
  - `python scripts/build-catalog.py --check`;
  - `bash scripts/check-drift.sh`;
  - `python scripts/check-docs-voice.py`;
  - `python scripts/validate-skills.py --channel all`;
  - `uv run ruff check src tests/eval`;
  - `uv run mypy`.

  Verify: all pass, apart from environment-only skips that also skip on `main`.
- [ ] 6.2 Run `openspec validate repo-cleanup` and `openspec validate --all`. Verify: both pass.
- [ ] 6.3 Open a PR against `main` (ask before posting). Verify: the required checks pass.

## 7. Initial check

- [ ] 7.1 After merge, check the removals and moves in use: one full CI run on `main`, one local run of the checks in `AGENTS.md` or CONTRIBUTING, and the next contributor PR. Write down anything that broke or got harder. If a decision in `design.md` turns out wrong or risky, propose the change to the maintainer and update `design.md`. Verify that the findings are recorded in this change.
