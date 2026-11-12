## Purpose

Lets the eval harness run Claude Code sessions on a pinned, low-cost model through OpenRouter, so the evals can run from a MarketSquare-owned key without a Claude subscription, while keeping cost and model choice under the same policy as Claude runs.

## ADDED Requirements

### Requirement: Provider selection at run time

The harness SHALL support two providers: `anthropic` (the default) and `openrouter`. A batch, a trigger run and a single run SHALL accept `--provider`. Passing a model id from the OpenRouter allow-list SHALL select `openrouter` without the flag. Passing `--provider openrouter` with a Claude model id, or `--provider anthropic` with an OpenRouter model id, SHALL be refused before any session starts. Task YAMLs and trigger sets SHALL NOT declare a provider or an OpenRouter model id. The provider and the model id SHALL be recorded on every run and in every results file.

#### Scenario: OpenRouter model selects the provider

- **WHEN** a batch is started with `--model deepseek/deepseek-v4.1-flash` and no `--provider`
- **THEN** every session runs through OpenRouter, and each run records provider `openrouter` and model `deepseek/deepseek-v4.1-flash`

#### Scenario: Mismatched provider and model

- **WHEN** a batch is started with `--provider openrouter --model claude-haiku-5-5`
- **THEN** the harness refuses to start and names the OpenRouter models it permits

#### Scenario: OpenRouter model in a task YAML

- **WHEN** a task declares `model: deepseek/deepseek-v4.1-flash`
- **THEN** loading fails, and the error says OpenRouter models are run-time only

### Requirement: OpenRouter session environment

For an `openrouter` session the runner SHALL point Claude Code at OpenRouter's Anthropic-compatible endpoint and authenticate with the `OPENROUTER_API_KEY` environment variable. It SHALL map every Claude model alias Claude Code may use (Haiku, Sonnet, Opus and the subagent model) to the selected model, so that no request reaches a Claude model. It SHALL NOT pass `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` to the session. The key SHALL NOT appear in run records, transcripts copied into results, reports or logs written by the harness. A run whose reported model usage names any model other than the selected one SHALL be recorded as incomplete with reason `provider_model`, naming the other models, and SHALL NOT be graded or counted as passing.

#### Scenario: Missing key

- **WHEN** an OpenRouter batch starts and `OPENROUTER_API_KEY` is unset or empty
- **THEN** the harness refuses to start and names the variable

#### Scenario: Claude credentials are not forwarded

- **WHEN** an OpenRouter session starts on a machine where `CLAUDE_CODE_OAUTH_TOKEN` is set
- **THEN** the session's environment does not contain that token or `ANTHROPIC_API_KEY`

#### Scenario: Unexpected model in the usage

- **WHEN** an OpenRouter session's result reports usage for `claude-haiku-5-5`
- **THEN** the run is recorded as incomplete with reason `provider_model` naming `claude-haiku-5-5`, and the gate does not count it as passing

### Requirement: OpenRouter model allow-list

The harness SHALL permit OpenRouter model ids only from a run-time allow-list kept in the harness code. That list SHALL start with `deepseek/deepseek-v4.1-flash`. Any other OpenRouter id SHALL be rejected, and the error SHALL name the permitted ids. Adding an id to the list SHALL require a price-table entry for it (see "Provider-priced cost").

#### Scenario: Unlisted OpenRouter model

- **WHEN** a batch is started with `--model z-ai/glm-5.3-flash`
- **THEN** the harness refuses to start and lists the permitted OpenRouter ids

### Requirement: Provider-priced cost

For `openrouter` runs the harness SHALL compute each run's cost from its reported token counts (input, cache reads, cache writes and output) and a per-model price table in USD per million tokens. It SHALL NOT use Claude Code's `total_cost_usd` for these runs. That computed cost SHALL be what `--max-cost-usd`, the pre-dispatch estimate, the results files and the reports use. Reports SHALL label it as an estimate from list prices.

#### Scenario: Cap uses the computed cost

- **WHEN** an OpenRouter batch runs with `--max-cost-usd 2` and its sessions report Claude-priced `total_cost_usd` totalling $30 but computed costs totalling $0.90
- **THEN** the batch is not stopped by the budget and records $0.90

#### Scenario: Report labels the estimate

- **WHEN** a report is rendered for OpenRouter runs
- **THEN** the cost column is marked as estimated from OpenRouter list prices

### Requirement: Turn-limit factor

A batch and a single run SHALL accept `--max-turns-factor <f>` with `f` from 1.0 to 3.0 (default 1.0). Each session's turn limit SHALL be the task's `max_turns` multiplied by `f` and rounded up. The factor SHALL be recorded with each run. A run that ends because it reached the turn limit SHALL be recorded as such, so reports can count turn-limit stops per task and arm.

#### Scenario: Scaled limit

- **WHEN** a task declares `max_turns: 14` and the batch runs with `--max-turns-factor 1.5`
- **THEN** its sessions run with a limit of 21 turns, and each run records factor 1.5

#### Scenario: Turn-limit stops are visible

- **WHEN** two of three replicates of a task end by reaching the turn limit
- **THEN** the report shows 2 turn-limit stops for that task and arm, whether or not the runs passed
