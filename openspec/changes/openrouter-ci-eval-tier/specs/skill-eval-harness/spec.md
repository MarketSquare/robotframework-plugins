## MODIFIED Requirements

### Requirement: Model allow-list and cost policy

Task YAMLs and trigger sets SHALL declare a model from the allow-list `claude-haiku-5-5` or `claude-sonnet-5-5`. They SHALL NOT declare `claude-opus-5-5` or an OpenRouter model id as their own model. Any other model id SHALL be rejected at load time, and the error SHALL name the permitted ids; a retired Claude id SHALL also name its replacement. At run time the harness SHALL additionally permit `claude-opus-5-5` and the ids on the OpenRouter allow-list (capability `eval-model-providers`). Running with `claude-opus-5-5` SHALL require an explicit run-time opt-in flag, and SHALL be refused unless a cost cap is also given. Every batch SHALL accept a cost cap (`--max-cost-usd`). The running total SHALL be the reported cost for Claude runs and the provider-priced cost for OpenRouter runs. When the running total reaches the cap, the harness SHALL stop dispatching new runs, mark the unstarted runs as `incomplete` with reason `budget`, and exit non-zero.

#### Scenario: Outdated model id rejected
- **WHEN** a task declares `model: claude-sonnet-4-6`
- **THEN** loading fails with an error naming `claude-sonnet-5-5` as the replacement and listing the permitted model ids

#### Scenario: Opus requires opt-in and cap
- **WHEN** a batch is started with `--model claude-opus-5-5` but without the opt-in flag or without `--max-cost-usd`
- **THEN** the harness refuses to start and explains which flag is missing

#### Scenario: OpenRouter model permitted at run time only
- **WHEN** a batch is started with `--model deepseek/deepseek-v4.1-flash`
- **THEN** the harness accepts the model, while a task YAML declaring the same id fails to load

#### Scenario: Budget exhausted
- **WHEN** the cumulative cost (reported for Claude runs, provider-priced for OpenRouter runs) reaches `--max-cost-usd` during a batch
- **THEN** no further sessions start, the unstarted runs are recorded as `incomplete` (reason `budget`), and the command exits non-zero

### Requirement: Regression gate against a stored baseline

The repository SHALL contain a baseline results file for each gated tier and each model the CI gates on. Baselines for the Claude models SHALL stay at `plugins/<plugin>/evals/baselines/<tier>.json`; baselines for an OpenRouter model SHALL be stored at `plugins/<plugin>/evals/baselines/openrouter/<model name>/<tier>.json`, where `<model name>` is the part of the id after the `/`. For every task×arm a baseline SHALL record pass rate, replicate count, mean tokens, turns, duration and cost, along with the model id, the provider, the turn-limit factor, the harness version and a content hash of the task definition. A gate command SHALL compare a new treatment result with the stored baseline. When no baseline path is given, the gate SHALL use the default path for the model of the runs being gated. It SHALL fail when a gating task's treatment pass rate is below the baseline: by default, when the baseline entry has at least 6 replicates, a one-sided Fisher exact test on pass/fail counts with p < 0.05; with fewer baseline replicates or an explicit tolerance, a drop of more than the tolerance (default: more than one replicate's worth, i.e. > 1/N). It SHALL also fail when mean input tokens rise by more than the configured budget (default 30%; the PR job MAY pass a wider budget calibrated from measured run-to-run variance). For trigger results, the gate SHALL compare each skill's validation split with the stored trigger baseline of the same model: when the baseline records run-level counts, skill loads on should-trigger runs and non-loads on should-not-trigger runs SHALL each be compared with a one-sided Fisher exact test (p < 0.05); otherwise accuracy may not drop by more than one query. The gate SHALL also fail when any shipped skill's description was listed by name only in a recorded skill listing. Tasks whose definition hash, model or turn-limit factor differs from the baseline entry SHALL be reported as `rebaseline-needed` and excluded from the comparison. They SHALL NOT be treated as passing. Updating the baseline file SHALL be an explicit command whose output is committed via a reviewed pull request; that command SHALL write to the default path for the runs' model unless an output directory is given.

#### Scenario: Pass-rate regression
- **WHEN** a gating task had baseline treatment pass rate 1.00 (N=3) and the new run has 0.33
- **THEN** the gate fails and names the task and both pass rates

#### Scenario: Flaky task against a 9-run baseline
- **WHEN** a gating task had baseline treatment pass rate 5/9 and the new run has 1/3
- **THEN** the gate passes (Fisher p = 0.24); against a 9/9 baseline, 1/3 fails (p = 0.045)

#### Scenario: Token budget regression
- **WHEN** a task's mean input tokens rise by 45% against the baseline with the default 30% budget
- **THEN** the gate fails and names the task and the increase

#### Scenario: Borderline trigger queries are not a regression
- **WHEN** a skill's baseline has two should-trigger queries that each loaded the skill in 3 of 6 runs, and a PR sample of 3 runs loads them once each
- **THEN** the trigger gate passes, because run-level loads are not significantly lower

#### Scenario: Description listed by name only
- **WHEN** a trigger session's skill listing shows `rf-setup` without its description
- **THEN** the gate fails with a `listing` finding for rf-setup that points to the listing-room test

#### Scenario: Changed task needs rebaseline
- **WHEN** a task's definition changed since the baseline was recorded
- **THEN** the gate reports the task as `rebaseline-needed` and does not count it as passing

#### Scenario: Baseline chosen by model
- **WHEN** the gate runs without `--baseline` on narrow-tier runs of `deepseek/deepseek-v4.1-flash` for rf-core
- **THEN** it compares them with `plugins/rf-core/evals/baselines/openrouter/deepseek-v4.1-flash/narrow.json`, not with the Haiku baseline

#### Scenario: Different turn-limit factor needs rebaseline
- **WHEN** the baseline entry was recorded with turn-limit factor 1.5 and the new runs used 1.0
- **THEN** the gate reports the task as `rebaseline-needed`

### Requirement: Tiered CI execution with bounded cost

CI SHALL run the harness in tiers, on a CI provider chosen per run: the OpenRouter tier (`deepseek/deepseek-v4.1-flash` with the turn-limit factor recorded in its baselines) whenever the `OPENROUTER_API_KEY` secret is available, and the Claude tier otherwise or when a manual run asks for it. On pull requests that touch skills, the plugin, eval tasks or the harness, CI SHALL run the narrow tier in the treatment arm with N=3 on the CI provider's model. That run SHALL be scoped to tasks of changed skills plus bundle canaries and SHALL be gated against the stored baseline of that model. On pull requests that change a skill's frontmatter `description`, CI SHALL run that skill's trigger set on the validation split on the same model. On a weekly schedule and on manual dispatch, CI SHALL run all tiers in both arms plus all trigger sets, and SHALL publish the report and a candidate baseline for the model it ran as artifacts. A manual dispatch SHALL accept the provider (`openrouter` or `claude`) and, for `claude`, the Claude model; Claude runs SHALL NOT start on pull requests or the schedule while the OpenRouter key is available. Every CI invocation SHALL pass an explicit cost cap. Every OpenRouter job SHALL report the key's actual spend during the job, read from OpenRouter before and after the runs, in its summary. When credentials are not available (for example fork PRs), the job SHALL report that evaluation was not run. It SHALL NOT report success.

#### Scenario: PR scoped to changed skill
- **WHEN** a pull request only changes `skills/rf-selenium/` and the OpenRouter key is available
- **THEN** CI runs the selenium narrow tasks and the bundle canaries in the treatment arm with N=3 on `deepseek/deepseek-v4.1-flash`, and gates them against that model's stored baseline

#### Scenario: Description change triggers trigger eval
- **WHEN** a pull request changes the `description` in a skill's SKILL.md frontmatter
- **THEN** CI runs that skill's validation trigger queries on the CI provider's model and reports precision and recall against that model's stored trigger baseline

#### Scenario: Manual Claude run
- **WHEN** a maintainer dispatches the evaluation with provider `claude` and model `claude-sonnet-5-5`
- **THEN** the job runs on the Claude credentials, gates against the Claude baselines and publishes a Claude candidate baseline

#### Scenario: Spend reported
- **WHEN** an OpenRouter PR job finishes
- **THEN** its summary shows the key's spend during the job in USD next to the harness's estimated cost

#### Scenario: Fork PR without secrets
- **WHEN** CI runs on a pull request where no OpenRouter key or Claude credentials are available
- **THEN** the evaluation job reports "not run: no credentials" and does not post a passing result
