# Guide for coding agents

Facts and commands for working in this repository. The rules for AI-assisted contributions are in [AI_POLICY.md](AI_POLICY.md); the full contributor guide is [CONTRIBUTING.md](CONTRIBUTING.md).

## Layout

- `plugins/<name>/`: one folder per plugin and the only copy of its content (skills, agents, hooks, hook scripts, `catalog.yaml`). Its `tests/` and `evals/` are not installed.
- `bundles/rf-agentskills/`: generated copy of the plugins listed in `plugins/rf-agentskills/catalog.yaml`.
- `installer/`: the `robotframework-plugins` package on PyPI.
- `src/rf_skill_eval/`: the eval harness (internal, never published); `eval/` holds its fixture projects and hidden graders.
- `security/`: scanner configuration and the reviewed baselines per plugin.
- `tests/`: shared tests (repository, catalogue, installer, harness in `tests/eval/`).
- `scripts/`: build and check utilities. `templates/plugin/`: starter plugin. `legacy/`: the one-shot `rf-agentskills` forwarder.
- `openspec/`: specs (`specs/`) and planned changes (`changes/`). `docs/archive/` is history; don't follow it.

## Checks

Set up first: `uv sync --all-packages`, then `uv run rfbrowser init chromium` for the browser tests (see [CONTRIBUTING.md](CONTRIBUTING.md)). Run the commands below in that environment, with `uv run` or the activated `.venv`.

CI (`.github/workflows/ci.yml`) runs these on every PR; run the ones your change touches before you push:

- `python scripts/build-catalog.py --check`
- `python scripts/check-governance.py`
- `python scripts/validate-skills.py --channel all`
- `python3 scripts/check-plugin-references.py`
- `python scripts/check-skill-keywords.py --require-all`
- `python scripts/check-robotcode-first.py`
- `bash scripts/check-drift.sh`
- `python scripts/check-docs-voice.py`
- `python -m pytest tests/test_marketplace_validation.py -v`
- `python -m pytest tests/ --ignore=tests/eval -v --tb=short`
- `python -m pytest plugins/<name>/tests -v --tb=short`
- `ruff check plugins/*/skills/*/scripts/*.py --select E,F,W --ignore E501`

The eval harness has its own suite: `uv sync --all-extras`, then `uv run pytest tests/eval`, `uv run ruff check src tests/eval` and `uv run mypy`.

The security gate (`.github/workflows/security-gate.yml`) also runs `python3 scripts/check_content_rules.py` and scans each changed plugin. Locally: `scripts/install-scanners.sh`, then `scripts/security-scan.sh <plugin> out/`.

## Generated files

Never edit these by hand. Change the source, run the command, and name the command in the PR.

| Files | Command |
|---|---|
| `.claude-plugin/marketplace.json`, `docs/catalog.md`, `bundles/rf-agentskills/`, the plugin list in `.github/ISSUE_TEMPLATE/plugin-feedback.yml` | `python scripts/build-catalog.py` |
| `plugins/*/variants/` (Codex and OpenCode subagents, OpenCode hook plugin) | `python scripts/build-agent-variants.py` |
| Plugin versions in `plugin.json` and skill `metadata.version` | `scripts/bump-version.sh <plugin> <major\|minor\|patch>`, then `python scripts/build-catalog.py` |
| `plugins/*/evals/baselines/` | A maintainer commits them from the `skill-evaluation.yml` candidate artifact |
| `uv.lock` | `uv lock` |

To change a skill that the bundle copies, edit it under `plugins/<name>/` and run `python scripts/build-catalog.py`; never edit `bundles/`.

## Never commit

- `.env` or any key or token; secret scanning and push protection block recognised secrets.
- Eval run output (`eval/runs/`, `eval/reports/`) and Robot Framework output (`output.xml`, `log.html`, `report.html`).
- Scanner output (`out/`, `.scanners/`), virtual environments and caches.
- Your own agent configuration and notes (`.claude/`, `.codex/`, personal memory files, scratch files at the root).

Write eval output outside the repository, for example `--output /tmp/rf-eval/...`.

## OpenSpec workflow

Changes beyond a small fix start as an OpenSpec change in `openspec/changes/<name>/`: `proposal.md` (why and what), `specs/<capability>/spec.md` (requirement deltas), `design.md` (how) and `tasks.md` (steps, each with a verify clause). Create it with `openspec new change <name>`, then:

1. Implement the tasks in order and tick each one only when its verify step passed.
2. Run `openspec validate --all --strict`.
3. After the PR merges, archive the change; that merges its deltas into `openspec/specs/`.

## RobotCode first

The [`robotcode` CLI](https://robotcode.io/guides/cli/) is the core of the Robot Framework AI toolstack. Use it for every capability below instead of writing a new implementation: no own parsing of `.robot` files to resolve keywords, no running `robot` and parsing `output.xml` for results, no libdoc builds to look up keywords. Custom code that calls `robotcode` and adds project logic is fine. When `robotcode` lacks something, raise it upstream with an issue or PR at [robotcode](https://github.com/robotcodedev/robotcode); a script that bridges the gap names that issue in a comment.

| Need | Command | Guide |
|---|---|---|
| Run tests with the project's settings | `robotcode robot` (alias `run`) | [CLI reference](https://robotcode.io/reference/cli/#robot) |
| List tests, tasks, suites and tags | `robotcode discover` | [Discovering tests](https://robotcode.io/guides/cli/discovering-tests/) |
| Static analysis | `robotcode analyze code` | [Analyzing code](https://robotcode.io/guides/cli/analyzing-code/) |
| Read a finished run's results | `robotcode results` | [Analyzing results](https://robotcode.io/guides/cli/analyzing-results/) |
| Run keywords step by step | `robotcode repl` | [REPL](https://robotcode.io/guides/cli/repl/) |
| Debug a failing suite | `robotcode robot-debug` | [Debugging](https://robotcode.io/guides/cli/robot-debug/) |
| Keyword and library documentation | `robotcode doc keyword`, `robotcode doc keywords` | [Browsing documentation](https://robotcode.io/guides/cli/browsing-documentation/) |
| Run through a wrapper (e.g. `uv run`) | `robotcode --wrapper …` | [Wrapper](https://robotcode.io/guides/cli/wrapper/) |
| Settings and profiles from `robot.toml` | `robotcode config`, `robotcode profiles` | [Profiles](https://robotcode.io/guides/robot-toml/profiles/) |

## Policy

Before you open a PR, read [AI_POLICY.md](AI_POLICY.md): you own the change, disclose substantial AI help in the PR's "AI assistance" section, and paid eval runs are for maintainers.
