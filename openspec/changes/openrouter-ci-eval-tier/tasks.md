## 1. Model policy and provider

- [x] 1.1 Add `OPENROUTER_MODELS` (`deepseek/deepseek-v4.1-flash`) to `domain/task.py`, permitted at run time and rejected in task YAML and trigger sets with a "run-time only" message. Verify with new cases in `tests/eval/test_domain_task.py` and `test_task_yaml_loading.py` (YAML rejected, run time accepted, unlisted `z-ai/glm-5.3-flash` rejected with the permitted ids named).
- [x] 1.2 Add a `Provider` value (`anthropic`, `openrouter`), derived from the model id, plus a `--provider` option on `run`, `run-batch` and `trigger` that refuses mismatched pairs before any session starts. Verify with CLI tests for the mismatch error and the derived default.
- [x] 1.3 Record the provider, the model and the turn-limit factor on every run (a new column in `runs`, migrated like the earlier columns) and in results and baseline entries. Verify with `test_persistence.py` (an old database opens, new runs store the provider) and `test_baseline_gate.py` (entries carry the provider and the factor).

## 2. Session environment and auth

- [x] 2.1 Make `ClaudeCodeRunner._build_env` provider-aware (design D1). For OpenRouter:
  - drop `CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_API_KEY` and any inherited `ANTHROPIC_AUTH_TOKEN`;
  - set the base URL, `ANTHROPIC_AUTH_TOKEN` from `OPENROUTER_API_KEY`, and the four model mappings;
  - raise `AuthConfigError` naming `OPENROUTER_API_KEY` when it's missing.

  Verify with runner unit tests that inspect the built environment for both providers.
- [x] 2.2 Make `config.has_auth` and `cli._require_auth` provider-aware, and make `doctor` report which credential the selected provider needs. Verify with `test_cli_doctor.py` cases for both providers.
- [x] 2.3 Record a run as incomplete with reason `provider_model` when its `modelUsage` names any model other than the selected one (the same way arm leaks are recorded), so it is not graded or counted as passing. Verify with a recorded-transcript test in `test_infrastructure_session_parser.py` and a gate test.
- [x] 2.4 Check that the key never reaches stored output: grep a fake key through a full fake batch's database, reports and copied config. Verify with a test that fails if the fake key string appears anywhere under the output dir.

## 3. Cost and turn limits

- [x] 3.1 Add `PROVIDER_PRICES` and compute the cost of OpenRouter runs from the usage block (input, cache read, cache write, output). Store it in `total_cost_usd` and record `cost_source` as `priced`. Verify with unit tests that check the arithmetic and that the budget stops on priced cost, not on Claude Code's reported cost.
- [ ] 3.2 Calibrate the DeepSeek prices against the spike: re-score the 72 spike transcripts with the price table. They're in the artifact `spike-openrouter-narrow` of run 42822700497 (`gh run download 42822700497 -n spike-openrouter-narrow`; it expires 90 days after 2026-11-10). Verify that the priced total is within ±25% of the $0.84 OpenRouter charged, and record both numbers in the PR.
- [x] 3.3 Label priced costs as estimates in the md/json reports. Verify with a `test_reporting.py` snapshot.
- [x] 3.4 Add `--max-turns-factor` (1.0–3.0, rounded up) to `run` and `run-batch`, record turn-limit stops from `subtype: error_max_turns`, and show the stop counts per task and arm in reports. Verify with a runner test asserting `--max-turns 21` for `max_turns: 14` at factor 1.5, and a report test for the stop count.

## 4. Per-model baselines and gate

- [x] 4.1 Derive the default baseline path from the runs' model (`baselines/openrouter/<model name>/<tier>.json` for OpenRouter, unchanged for Claude) in `gate`, `report` and `baseline update`. Verify with `test_baseline_gate.py` cases for both defaults and an explicit `--baseline` override.
- [x] 4.2 Make a turn-limit factor mismatch a `rebaseline-needed` finding. Verify with a gate test for factor 1.5 against 1.0.
- [x] 4.3 Remove the spike's `RF_SKILL_EVAL_EXTRA_MODELS` and `ANTHROPIC_AUTH_TOKEN` auth shortcuts, so they don't come back through a merge from the spike branch. Verify with `grep -r RF_SKILL_EVAL_EXTRA_MODELS src tests` returning nothing, and with `uv run ruff check src tests/eval`, `uv run mypy` and `uv run pytest tests/eval -q` all green.

## 5. CI workflow

- [x] 5.1 Make preflight in `skill-evaluation.yml` output `provider`, `model`, `turns_factor` and the baseline subdirectory: OpenRouter when `OPENROUTER_API_KEY` is set, otherwise Claude, with a `provider` dispatch input overriding both. Keep the fork-PR rule. Verify with `tests/eval/test_ci_preflight.py` cases and by checking that the workflow still parses (`uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/skill-evaluation.yml'))"`).
- [ ] 5.2 Wire `pr-eval` and `full-eval` to the preflight outputs:
  - the model and the turn-limit factor;
  - the credentials for the provider only;
  - separate OpenRouter caps (`*_CAP_USD_OPENROUTER`);
  - the baseline paths for the model;
  - the candidate-baseline artifact names, which include the model.

  Verify on a PR from a branch in this repository: the eval job runs on DeepSeek and gates against the OpenRouter baselines.
- [ ] 5.3 Add the steps for OpenRouter jobs:
  - a one-session smoke step that fails fast;
  - "Spend before" and "Spend after" steps that read `/api/v1/key`;
  - a summary line with the key's spend during the job next to the priced total;
  - on the weekly job, a warning when they differ by more than 25%.

  Verify in the job summary of the PR run from 5.2.
- [ ] 5.4 Check the no-credentials path: dispatch with provider `openrouter` from a fork, or with the secret temporarily unavailable through an environment that lacks it, and see "not run: no credentials". Verify from the run summary. If testing this needs a secret removed, ask the maintainer first.

## 6. Baselines

- [ ] 6.1 Dispatch the evaluation with provider `openrouter`, all tiers, both arms, N=6 and factor 1.5, for every plugin with evals. Verify that the run completes within the OpenRouter caps and produces one candidate baseline per plugin.
- [ ] 6.2 Review the candidate baselines (flaky tasks, turn-limit stops, and whether 1.5 is enough), commit them under `plugins/<plugin>/evals/baselines/openrouter/deepseek-v4.1-flash/` in a reviewed PR, and record the reviewed spend. Verify that the next PR eval run reports the gate as `pass`, not `rebaseline-needed`.

## 7. Docs and clean-up

- [x] 7.1 Update `docs/ci/usage.md` and `docs/ci/local-testing.md` (running on OpenRouter locally, the key, `--provider`, `--max-turns-factor`, priced cost, where the baselines live) and add a dated addendum to ADR-005 for the default-provider change. Verify with `uv run pytest tests -q -k "docs or stale or links"` and by reading the rendered files.
- [x] 7.2 Add "manual Claude eval (provider `claude`, Sonnet 5.5, narrow and realistic)" to the release checklist in `RELEASING.md`. Verify that the checklist renders and names the dispatch inputs.
- [ ] 7.3 Delete the branch `spike/openrouter-evals` locally and on origin (it holds the spike workflow), after asking the maintainer. Verify that `git ls-remote origin spike/openrouter-evals` prints nothing.
- [ ] 7.4 Run `openspec validate openrouter-ci-eval-tier --strict` and confirm it passes before the archive.
