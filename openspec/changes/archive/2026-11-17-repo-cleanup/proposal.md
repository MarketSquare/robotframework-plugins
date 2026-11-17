## Why

The repository grew out of the single-plugin `rf-agentskills` repository, and the move left files that nothing runs, dependencies nothing imports, and a few tools that no longer work. New contributors, human or AI, can't tell which parts matter, and the stale parts give wrong instructions. This change removes what is unused and fixes what is broken or conflicting, with no change for users of the plugins or the installer.

## What Changes

- **Root config:** delete `.mcp.json` (registers `claude-flow` and an `rf-mcp` command nothing reads).
- **Eval harness dead code:** remove modules, errors, constants and settings that have no caller, and the treatment-arm path that merges a plugin `.mcp.json` (no plugin ships one, and the catalogue forbids it).
- **Dependencies:** drop `scipy`, `numpy`, `httpx` and `polars` from the harness, the duplicate `validation` extra, and stale `pyproject.toml` entries (the sdist exclude list, the `skills` ruff exclude, the "legacy plugin tests" comment). Regenerate `uv.lock`.
- **CI and release:**
  - delete `update-latest.yml`, which force-pushes `latest` to `main` while `release.yml` points it at release tags;
  - delete the unused `.github/actions/setup-eval`;
  - run each check once (`validate-skills.py` and the agent-variants check run twice today);
  - stop building the Codex and Copilot symlink tarballs that no release ships;
  - stop exporting the skills twice in the release.
- **Scripts:** delete `scripts/validate-marketplace.py` (covered by `build-catalog.py --check` and the marketplace tests) and the broken Docker test harness (`scripts/docker-test-harness.sh`, `docs/installer/docker*`). Fix old names in `build-skill-zips.py`, `build-description-variant.py` and `scripts/templates/opencode-plugin.js`.
- **Docs:**
  - move dated plans, one-off reports, proposals and raw logs to `docs/archive/`;
  - narrow the old-repository-name exemption in `tests/test_repository_references.py` from all of `docs/` to the archive and the ADRs;
  - fix the factual errors in the current guides (`docs/ci/usage.md`, `local-testing.md`, `faq.md`, `plugins/rf-core/hooks/README.md`, the README "Prerequisites" line);
  - repoint source comments that link to moved files.
- **Specs:** update main-spec requirements that still require the root `skills/` tree, the sync script or plugin MCP servers. Requirements already covered by the unarchived `launch-plugin-programme` change are left to it.

Kept on purpose (see design.md):
- the `bundles/rf-agentskills` bundle;
- `legacy/rf-agentskills` until the forwarder release 0.9.0 is on PyPI;
- the installer's migration code for the old marketplace;
- the install-record names.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-eval-harness`: the treatment arm provisions skills, hooks and subagents; plugin MCP servers are no longer part of it.
- `skill-metadata-conformance`: references use `plugins/<plugin>/skills/rf-<topic>/` paths, and the release-package scenario names only the packages a release ships.
- `skill-catalog`: the generator-skill ban lists the channels that exist today.
- `python-library-skill`, `language-skill`, `platynui-skill`, `setup-skill`, `library-skill-structure`: skill locations are `plugins/<plugin>/skills/…`, and distribution goes through the plugin, the bundle copy and the installer assets instead of a sync script.

## Impact

- **Code:** `src/rf_skill_eval/` (deletions only; no CLI command changes), `tests/eval/` (tests of removed code go), `tests/test_repository_references.py`.
- **Config:** `pyproject.toml`, `uv.lock`, `.env.example`, `.mcp.json` (deleted).
- **CI:** `.github/workflows/ci.yml`, `release.yml`, `update-latest.yml` (deleted), `.github/actions/setup-eval/` (deleted). The required check names stay the same.
- **Scripts:** `scripts/validate-marketplace.py`, `scripts/docker-test-harness.sh` (deleted); three scripts get comment and name fixes; the regenerated OpenCode variant.
- **Docs:** about 15 files move to `docs/archive/`; `docs/installer/docker*` is deleted; current guides are corrected.
- **Users:** none. Plugins, the bundle, the installer and the release artifacts stay the same, except the unreleased CI-only Codex and Copilot tarballs.
- **Related changes:** `ai-contributor-docs` rewrites the contributor docs (this change only fixes factual errors). `lean-governance` reconciles and archives `launch-plugin-programme`, which fixes the remaining sync-era requirements.
