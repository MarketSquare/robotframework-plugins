## Context

The harness drives the real Claude Code CLI (`claude -p`) in an isolated config dir per run, and Claude Code talks to whatever Anthropic-compatible endpoint `ANTHROPIC_BASE_URL` names. The spike on `spike/openrouter-evals` proved this works with OpenRouter, using a few changes:
- an extra-models environment variable for the allow-list;
- accepting `ANTHROPIC_AUTH_TOKEN` as credentials;
- a workflow that set the OpenRouter variables itself.

Today:
- `ClaudeCodeRunner._build_env` copies the whole process environment and requires `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY`.
- `domain/task.py` holds the Claude allow-lists.
- `Budget.charge` adds Claude Code's `total_cost_usd`.
- The gate reports any model mismatch as `rebaseline-needed` and exits 3.
- `skill-evaluation.yml` runs PR jobs on Haiku and weekly jobs on the tier defaults, with OAuth credentials.

Spike numbers used below (run 42822700497, rf-core narrow, 72 sessions):
- actual spend $0.84, with 16.6M input tokens (mostly cache reads) and 376k output tokens;
- Claude Code's own total was $29.66;
- 25 sessions stopped at `max_turns`;
- mean turns were 13–20, against 2–18 for Haiku.

## Goals / Non-Goals

**Goals:**
- The provider is a harness concept, not a workflow trick. The same command works locally and in CI.
- The cap, the estimate and the reports use a cost that is close to what OpenRouter charges.
- Claude and DeepSeek results never get compared with each other by accident.

**Non-Goals:**
- Supporting arbitrary OpenRouter models, or any other gateway (LiteLLM, Bedrock). The allow-list stays short on purpose.
- Changing task definitions or graders to suit DeepSeek.
- Tuning skill content for DeepSeek. The skills are written for Claude, and the cheap tier is a regression signal, not a target.
- Removing the Claude tier or its baselines.

## Decisions

### D1. A provider value in the harness, derived from the model id

`--provider {anthropic,openrouter}` exists for clarity, but the model id already decides it: ids containing `/` come from the OpenRouter list. The runner builds the session environment per provider:
- **openrouter:**
  - start from the process environment minus `CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN`;
  - set `ANTHROPIC_BASE_URL=https://openrouter.ai/api`, `ANTHROPIC_AUTH_TOKEN=$OPENROUTER_API_KEY` and `ANTHROPIC_API_KEY=""`;
  - set `ANTHROPIC_DEFAULT_{HAIKU,SONNET,OPUS}_MODEL` and `CLAUDE_CODE_SUBAGENT_MODEL` to the model.
- **anthropic:** unchanged.

The auth checks in `config.py` and `cli.py` follow the provider.

*Alternative:* keep the spike's approach, where the workflow sets the variables and the harness only allows extra ids. That was rejected: local runs would need the same hand-set environment, the credential check would accept any `ANTHROPIC_AUTH_TOKEN`, and nothing would stop Claude credentials from leaking into a session that should be on OpenRouter.

### D2. A run-time OpenRouter allow-list next to the Claude lists

Add `OPENROUTER_MODELS = frozenset({"deepseek/deepseek-v4.1-flash"})` in `domain/task.py`:
- `ALLOWED_MODELS` (run time) includes it;
- `YAML_ALLOWED_MODELS` does not.

The spike's `RF_SKILL_EVAL_EXTRA_MODELS` variable is dropped. An allow-list that an environment variable can extend isn't an allow-list.

*Alternative:* allow any `vendor/model` id. That was rejected, because each new model needs its own baselines and a price entry, so adding one should be a reviewed code change.

### D3. Cost from a price table, checked against OpenRouter

`PROVIDER_PRICES[model] = {input, cache_read, cache_write, output}` in USD per million tokens. The cost is computed from the stream's `usage` block when the run is recorded and stored in the existing `total_cost_usd` column; a new `cost_source` column says `reported` or `priced`. So `Budget`, `estimate_cost`, the results files and the reports need no other changes.

The table is calibrated against the spike: priced cost over the spike's 72 runs should come within ±25% of the $0.84 OpenRouter charged. The figure that counts is still the key's spend that CI reads from OpenRouter (D7).

*Alternatives:*
- Query OpenRouter's per-generation endpoint for each request. That's exact, but Claude Code doesn't expose generation ids, and it adds network calls to the runner.
- Use only the key's spend before and after. That's exact per job, but it can't drive a per-run cap.

### D4. Turn-limit factor, recorded and gated

`--max-turns-factor` multiplies `task.max_turns` and rounds up, with 3.0 as the upper bound. The factor goes into the run record and the baseline entries, and a different factor means `rebaseline-needed` (see the spec). The OpenRouter tier starts at 1.5, chosen from the spike: 25 of the 72 sessions hit the limit with factor 1.0. The weekly baseline run decides whether 1.5 is enough. A turn-limit stop is recorded from the result's `subtype: error_max_turns`.

*Alternative:* separate `max_turns` per provider in each task YAML. That was rejected: 50+ YAMLs to keep in step, and task hashes would change for Claude too.

### D5. Per-model baseline paths

Claude baselines stay at `baselines/<tier>.json`, so no file moves and no history is lost. OpenRouter baselines go to `baselines/openrouter/<model name>/<tier>.json`. `gate` and `baseline update` derive the default path from the runs' model. CI passes the path explicitly anyway, so a misdetected model can't silently select the wrong file.

*Alternative:* one baseline file with entries keyed by model. That was rejected: it changes the schema for every consumer and makes Claude rebaselines touch DeepSeek entries.

### D6. CI picks the provider once, in preflight

Preflight outputs `provider` and `model`:
- `openrouter` when `OPENROUTER_API_KEY` is set;
- else `claude` when Claude credentials are set;
- a manual dispatch input `provider` overrides both.

The `pr-eval` and `full-eval` jobs take the model, the turn-limit factor, the credentials and the baseline paths from those outputs. The fork-PR rule (a fork never has credentials) is unchanged. The caps stay in USD, but the OpenRouter ones get their own environment values (for example `PR_NARROW_CAP_USD_OPENROUTER: "2"`), since the Claude caps would never bind.

### D7. Spend reporting from the key endpoint

Before and after the runs, a step reads `GET https://openrouter.ai/api/v1/key` and records `usage`, `limit` and `limit_remaining`. The step summary shows the difference next to the harness's priced total. That was the spike's approach, and it worked. Concurrent jobs share the key, so the delta is labelled "key spend during this job (includes concurrent jobs)". `max-parallel: 1` on `full-eval` already keeps weekly runs sequential.

## Risks / Trade-offs

- **Unsupported model.** Claude Code may refuse or mishandle non-Claude models in a future release (today it only logs `unrecognized_model`). → CI installs Claude Code without a pinned version, so this would show up as a failed doctor or smoke step. Add a one-session smoke step to OpenRouter jobs that fails fast. The fallback is a manual Claude run, and pinning the last working Claude Code version.
- **Key exposure.** Agent sessions run plugin hooks and Bash with the session environment, and that includes the OpenRouter key as `ANTHROPIC_AUTH_TOKEN`. That's the same exposure the OAuth token has today. → Only maintainer-pushed code runs with the key (the fork rule is unchanged), and the key has a credit limit on a MarketSquare account and nothing else depends on it.
- **Routing drift.** OpenRouter may serve the model from different hosts with different quantisation or behaviour. → Pin the provider routing (`provider.order` / `allow_fallbacks: false` through OpenRouter's preferences, if Claude Code's request path allows it; otherwise record the serving provider from the response headers when available) and watch the weekly variance.
- **Signal quality.** DeepSeek's pass rates and arm deltas aren't Claude's. A skill change could help Claude and hurt DeepSeek, or the other way round. → A manual Claude run is part of the release checklist, and the reports name the model prominently.
- **Price drift.** The price table goes stale. → The weekly job compares the priced total with the key delta and warns when they differ by more than 25%.
- **Baselines on 3 replicates.** These are noisy (the spike had partial passes on 2 treatment tasks). → The first baseline is recorded from a weekly run with N=6 before the gate becomes required.

## Migration Plan

1. Land the harness changes. Claude behaviour is unchanged and the existing tests pass.
2. Run a manual dispatch with provider `openrouter`, all tiers, both arms, N=6, factor 1.5. Review the candidate baselines and commit them in a PR.
3. Switch the PR and weekly defaults to OpenRouter (D6) in the same PR or the next one. The gate now finds matching baselines.
4. Delete `spike/openrouter-evals` and its workflow.
5. **Rollback:** delete the `OPENROUTER_API_KEY` secret, or dispatch with provider `claude`. Preflight then falls back to the Claude tier and its untouched baselines.

## Open Questions

- Whether Claude Code forwards OpenRouter provider-routing preferences. If it doesn't, routing stays OpenRouter's default and we record what we can. This changes neither the specs nor the tasks.
- The exact OpenRouter caps for PR and weekly jobs. They get set after the first weekly run, as the Claude caps were.
