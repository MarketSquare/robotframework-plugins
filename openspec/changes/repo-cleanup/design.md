## Context

See proposal.md (Why). Facts that shape the approach, checked at `56547f0`:

- **Required checks** on `main` include "Validate plugin structure", "Check generated variants and plugin layout", "Lint", "Template plugin passes the PR checks" and the six "Test (…)" jobs. "Build Claude Code plugin", "Build portable skills packages" and "Validate SKILL.md frontmatter (agentskills.io)" are not required.
- **Duplicate checks:**
  - `ci.yml` runs `scripts/validate-skills.py --channel all` in `validate-plugin` (`:213`) and again in `validate-skills` (`:287`);
  - it runs `scripts/build-agent-variants.py --check` in `validate-plugin` (`:211`) and again through `scripts/check-drift.sh:107`.
- **`build-claude-plugin`** (`ci.yml:298-343`):
  - its inline Python repeats checks that `validate-skills.py` and `check-drift.sh` already make, except one: the ban on a plugin `.mcp.json` or `servers/`;
  - its tarball `rf-agentskills-claude-plugin.tar.gz` has no consumer, because `release.yml` builds its own archives.
- **`build-portable-skills`** (`ci.yml:345-395`) builds Codex and Copilot symlink tarballs. `release.yml` ships only `<plugin>-skills-<version>.tar.gz` and the skill zips.
- **Double export in the release:** `release.yml:83-85` runs `export-skills.py` and then `build-skill-zips.py --plugin`, which exports again because it doesn't get `--skills`.
- **The `latest` branch:**
  - `update-latest.yml` force-pushes `latest` to `main` after every green CI run;
  - `release.yml:124-129` moves `stable` and `latest` to each release tag;
  - RELEASING.md:30 documents only the release behaviour.
- **The harness stages the merged plugin content as `plugins/rf-agentskills`** (`application/variant.py:29`, `claude_code_runner.py:375`). This is the bundle's shape, built by `staging.merge_plugins`, not a pre-split leftover, so it stays.
- **The plugin MCP path:**
  - `claude_code_runner.py:261-268` and `:452-470` merge a staged plugin's `.mcp.json` into the treatment arm, and `:867-871` checks the baseline for leaks of those servers;
  - no plugin ships one, and `skill-catalog` "The bundle ships no MCP server" forbids it.
- **`RF_SKILL_EVAL_LOG_LEVEL` stays:** `configure_logging` reads it from the environment (`config.py:66`). Only the `Settings` field that mirrors it is unused. `CLAUDE_MODEL_DEFAULT` has no reader; task YAMLs and `domain/task.py` set the model.
- **Async tests:** there are none in `tests/`, `installer/` or `plugins/*/tests`. `pytest-asyncio` is installed only because both `pyproject.toml` files set `asyncio_mode = "auto"`.
- **The Docker harness** (`scripts/docker-test-harness.sh`, `docs/installer/docker/`) calls the `rf-agentskills` command and `installer/src/rf_agentskills/`. Neither has existed since the rename (`installer/pyproject.toml:69`). Nothing in CI runs it.
- **`tests/test_repository_references.py`** exempts all of `docs/` from the old-name check. Of the documents that would stay outside `docs/archive/`, only ADR-003 (`:65,70`) names the old repository.
- **`scripts/check-docs-voice.py:64`** checks `docs/**/*.md` except `docs/reports/`.

## Goals / Non-Goals

**Goals:**
- Every file in the repository is either used, or an archived record that says it is one.
- CI runs each check once, and the required check names don't change.

**Non-Goals:**
- **The harness ports/service layering** (`application/ports.py`, `evaluation_service.py`). It is a refactor, not a removal, and `robotcode-first-tooling` touches the same code.
- **Keyword resolution and the libdoc specs.** These belong to `robotcode-first-tooling`.
- **Contributor docs and governance:**
  - rewriting CONTRIBUTING, README structure or GOVERNANCE belongs to `ai-contributor-docs` and `lean-governance`;
  - reconciling `launch-plugin-programme` belongs to `lean-governance`.
- **Things kept on purpose:**
  - `bundles/rf-agentskills`: an active marketplace entry. It is a copy because agents don't install dependencies that an update adds.
  - `legacy/rf-agentskills`: deleted after 0.9.0 is on PyPI. PyPI is still at 0.8.0, and that release is a manual step.
  - The installer's old-marketplace and `rf-agentskills-files` migration: users of 0.x and 3.0.0 still upgrade through it.
  - The `rf-tools` cleanup (`cli.py:925-990`): removing it would change behaviour for upgrading users, so it gets its own deprecation.
  - The `rf-agentskills/installed.json` record names: renaming them would need a migration.

## Decisions

### D1. Archive, don't delete, the dated documents

Plans, reports, proposals and raw logs move to `docs/archive/` with `git mv`. They keep their names and are flattened only where two would clash. `docs/archive/README.md` holds one line per file: date, what it was, and what replaced it.

- The archive is excluded from `check-docs-voice.py` (like `docs/reports/`), because nobody edits historical text.
- `tests/test_repository_references.py` exempts `docs/archive/` and `docs/ci/architecture/adr/` instead of `docs/`. ADRs are immutable records; ADR-006 gets one status line saying the Parquet writer was removed.
- Source comments that link to moved files are repointed:
  - `installer/pyproject.toml:7`;
  - `installer/src/robotframework_plugins/__init__.py:7`, `adapters/codex.py:3`, `adapters/claude_code.py` and `transforms.py:721`;
  - the installer test docstrings;
  - `plugins/rf-core/hooks/README.md` (the bundle copy follows through `build-catalog.py`);
  - `eval/fixtures/README.md`, `plugins/rf-core/evals/tasks/README.md` and the ADRs.

Files that move: `marketplace-implementation-plan.md`, `skill-architecture-review.md`, `e2e-test-results.md`, `RF_AGENTSKILLS_ISSUE_REPORT.md`, `issues/*`, `installer/proposal.md`, `installer/docker-test-harness-proposal.md`, `plugin/hooks-fix-proposal.md`, `ci/implementation-plan.md`, `ci/rf-agentskills-eval-implementation-plan.md` and `ci/claude-code-extension-quality-evaluation.md`. `ci/architecture/ddd-design.md` ("Draft (v1)") moves too, and `docs/ci/usage.md` stops linking to it.

Alternative: delete them, since git keeps the history. That's rejected because the installer CHANGELOG and the source comments cite them as the record of why a fix was made, and a link to a commit is harder to follow.

### D2. Delete the Docker harness

It has been broken since the rename and nobody noticed, so nothing depends on it. The installer tests (fake agent CLIs, ubuntu and windows matrix) cover the installer logic.

The harness did one thing nothing else does: it installed into the real agent CLIs. That coverage is lost. If it's wanted back, the right form is a CI job with a current image, built from git history. `installer/CHANGELOG.md` keeps its historical entry.

Alternative: fix it. That's rejected for now: it needs seven agent CLIs installed in an image, and it would stay outside CI.

### D3. Harness removals are limited to code with no caller

A symbol is removed when nothing in `src/`, `tests/`, `scripts/`, `plugins/` or `.github/` imports or calls it, apart from its own unit test:
- `domain/events.py`, `domain/skill.py` and `infrastructure/persistence/parquet_writer.py`;
- `ConfigError`, `PersistenceError` and `VERDICT_STATUSES`;
- `Settings.claude_model_default` and `Settings.rf_skill_eval_log_level`;
- `ClaudeCodeRunner._extra_mcp_servers`, its call in `_mcp_servers` and the plugin-server leak check;
- `CLAUDE_MODEL_DEFAULT` in `.env.example` and `docs/ci/usage.md`.

The `config_builder.py` docstring stops mentioning `rf-tools`. The test `test_extra_mcp_servers_returns_substituted_servers` goes with its subject. The CLI commands, the run records and the scoring stay as they are.

### D4. Dependencies follow imports

- From the harness: drop `scipy`, `numpy` and `httpx` (no import) and `polars` (only the deleted writer), plus their mypy overrides.
- Drop the `validation` extra: it duplicates the dev group, and no document refers to it (the hooks README line was removed in `delegate-robotcode-skills`).
- Drop `pytest-asyncio` and `asyncio_mode = "auto"` from both `pyproject.toml` files and from the `pip install` lines in `ci.yml` (`:65`, `:169`, `:187`), since there are no async tests.
- Drop the sdist `exclude` list, because `include` already limits the sdist to five entries.
- Remove `skills` from the ruff excludes, and rewrite the `tests/test_*.py` comment to say the shared suite is linted by the `lint` job's own command.
- Regenerate `uv.lock` with `uv lock`.

Alternative: keep `rf-mcp[all]` lighter. Out of scope, because the eval tasks use its library set.

### D5. One run per check, same required names

- In `validate-plugin`, the `build-agent-variants.py --check` and `validate-skills.py` steps go. `check-drift` and `validate-skills` run them.
- `build-claude-plugin` goes. Its MCP and `servers/` ban moves into `scripts/check-drift.sh` as a "no plugin MCP server" section, so the required "Check generated variants and plugin layout" check keeps enforcing it.
- In `build-portable-skills`, the Codex and Copilot steps and their uploads go. The standalone tarball and the skill zips stay, because they are what a release ships and CI proves that they build.
- In `release.yml:85`, `build-skill-zips.py` gets `--skills skills`, so it reuses the export from `:83`.

Alternative: merge `validate-skills` into `validate-plugin`. That's rejected because it would drop a job name that branch protection or contributors may watch, for no gain.

### D6. `release.yml` owns `latest`

Delete `update-latest.yml`. After this change, `latest` moves only on a release, as RELEASING.md:30 already says.

Users who pinned the marketplace to `latest` stop getting unreleased `main` commits. That is the documented behaviour, and the mismatch with it was the bug. README, RELEASING and the installer README never tell users to pin `latest` (checked with `grep -n latest`).

### D7. Main specs: only what no other active change covers

`launch-plugin-programme` already removes or rewrites these sync-era requirements:
- library-skill-structure "Restructured skills are distributed";
- platynui-skill "Skill is integrated into distribution channels";
- setup-skill "Setup skill is distributed without drift";
- skill-content-verification;
- library-skill-install-guidance;
- skill-metadata-conformance "Sync propagates skills…";
- skill-catalog "Distribution tooling rejects orphaned copies" and "Retirements are released as a breaking content change" (the lockstep version).

This change modifies only the requirements that would still be wrong after that archive (see `specs/`). `skill-eval-harness` "Tiered CI execution" keeps its `skills/rf-selenium/` example: `openrouter-ci-eval-tier` modifies that requirement, so this change doesn't touch it, and that change's archive should fix the example.

## Risks / Trade-offs

- [Archiving `launch-plugin-programme` before or after this change collides on the same capability] → The deltas touch disjoint requirements, so either archive order works. Task 6.2 runs `openspec validate --all`.
- [A deleted script or workflow was used outside the repository] → Before deleting, grep the tree and the open PRs. The release notes of the next installer version name the removed scripts.
- [Removing `pytest-asyncio` breaks a future async test] → The test would fail loudly on collection; re-add the plugin then.
- [`uv lock` moves other pins] → Plain `uv lock` keeps the existing pins and only drops packages nothing needs. If the lock diff shows any other version change, investigate it before merging.

## Migration Plan

One PR, no release needed, since no shipped artifact changes. Roll back by reverting the PR. Everything removed stays in git history.
