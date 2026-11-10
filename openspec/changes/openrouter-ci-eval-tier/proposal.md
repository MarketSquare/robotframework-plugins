## Why

The live skill evals only run on Claude models, billed to a maintainer's Claude subscription (`CLAUDE_CODE_OAUTH_TOKEN`). MarketSquare can't run them without that person, and every PR and weekly run spends from their plan. A spike (run 42822700497, 2026-11-10) ran the rf-core narrow tier in both arms, N=3, through OpenRouter on `deepseek/deepseek-v4.1-flash`. All 72 sessions completed, the skills loaded in every treatment run, the treatment arm passed 11 of 12 tasks at 1.00, and the arm delta stayed visible on 8 tasks. OpenRouter charged $0.84 for the whole run. That makes a cheap tier, paid from a MarketSquare-owned key, a realistic default for CI.

## What Changes

- The harness can run sessions on a pinned OpenRouter model. A run-time `--provider openrouter` (or an OpenRouter model id) makes the runner point Claude Code at OpenRouter's Anthropic-compatible endpoint, map every Claude model alias and the subagent model to the chosen model, and authenticate with `OPENROUTER_API_KEY`. Task YAMLs keep declaring Claude models only.
- The model allow-list gains a run-time-only OpenRouter list, starting with `deepseek/deepseek-v4.1-flash`. Other OpenRouter ids are rejected like any unknown model.
- Cost for OpenRouter runs is computed by the harness from a per-model price table and the reported token counts, instead of Claude Code's `total_cost_usd`, which prices every model as Claude (the spike reported $29.66 for $0.84 of spend). `--max-cost-usd` and the pre-dispatch estimate use that figure.
- A run-time `--max-turns-factor` scales each task's `max_turns`. DeepSeek needs more turns than Haiku: 25 of the 72 spike sessions hit the limit.
- Baselines are stored per model. The OpenRouter tier gets its own baseline files next to the Haiku ones, and the gate compares each run only with the baseline of its model.
- **BREAKING (CI behaviour):** PR and weekly eval jobs run on the OpenRouter tier when `OPENROUTER_API_KEY` is set, gated against the OpenRouter baselines. Claude runs move to manual dispatch (`provider: claude`), for releases and for checking the cheap tier against Claude.
- CI reports the real OpenRouter spend of each job (the key's usage before and after) in the step summary. The key's credit limit on OpenRouter is the hard cap.
- The spike branch `spike/openrouter-evals` and its workflow are deleted.

## Capabilities

### New Capabilities

- `eval-model-providers`: running eval sessions through a non-Anthropic provider: the provider setting, the environment the runner builds, which OpenRouter models are allowed, how their cost is computed, and the turn-limit factor.

### Modified Capabilities

- `skill-eval-harness`:
  - "Model allow-list and cost policy": adds the run-time OpenRouter list and the provider-computed cost the cap uses; corrects the outdated Claude ids in the requirement text to the 5.5 models the code already enforces.
  - "Regression gate against a stored baseline": baselines are kept per model, and the gate picks the one that matches the run's model.
  - "Tiered CI execution with bounded cost": PR and weekly runs use the OpenRouter tier when its key is present; Claude runs are manual; jobs report the provider's real spend.

## Impact

- **Harness code:**
  - `src/rf_skill_eval/domain/task.py`: model lists.
  - `application/batch.py`: runtime policy and budget.
  - `infrastructure/runner/claude_code_runner.py`: environment and max turns.
  - `config.py` and `cli.py`: auth check and new flags.
  - The baseline and gate commands: the per-model path.
- **CI:** `.github/workflows/skill-evaluation.yml` (a provider input, credential detection, OpenRouter environment, spend steps, baseline paths).
- **Data:** new `plugins/<plugin>/evals/baselines/openrouter/deepseek-v4.1-flash/{narrow,partial,triggers}.json` for each plugin with evals, recorded by a reviewed PR.
- **Docs:** `docs/ci/usage.md`, `docs/ci/local-testing.md`, and a short addendum to ADR-005.
- **Secrets and accounts:** `OPENROUTER_API_KEY` in the repository, from a MarketSquare-owned OpenRouter account with a credit limit (already added for the spike). `CLAUDE_CODE_OAUTH_TOKEN` becomes optional.
- **Caveats:**
  - Anthropic does not support non-Claude models in Claude Code. Claude Code prints `unrecognized_model` on every session; it was harmless in the spike, but a future Claude Code release could break this path. The manual Claude tier is the fallback.
  - OpenRouter may route a model to different hosts, which can shift results between runs.
  - Results on DeepSeek say how the skills work with DeepSeek. They don't replace a Claude check before a release.
