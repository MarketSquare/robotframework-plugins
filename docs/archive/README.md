# Archive

Plans, reviews, proposals and raw logs from before the move to this repository. They're kept as the record of why something was built or fixed; source comments and changelogs link to them. Nothing here is current: don't follow their instructions, and don't edit them.

| Date | File | What it was | Replaced by |
|---|---|---|---|
| 2026-02-23 | [marketplace-implementation-plan.md](marketplace-implementation-plan.md) | Plan for the Claude Code plugin marketplace of `rf-agentskills` | The marketplace in `.claude-plugin/` and RELEASING.md |
| 2026-03-17 | [skill-architecture-review.md](skill-architecture-review.md) | Review of the root `skills/` tree and its sync to the plugin | One plugin per folder under `plugins/`, no root copy |
| 2026-03-17 | [e2e-test-results.md](e2e-test-results.md) | Manual test of skill portability across agents | The installer tests in `tests/installer/` |
| 2026-04-27 | [implementation-plan.md](implementation-plan.md) | Plan for CI-based skill evaluation | The eval harness, `docs/ci/usage.md` |
| 2026-04-27 | [rf-agentskills-eval-implementation-plan.md](rf-agentskills-eval-implementation-plan.md) | First plan of the eval harness, with a flat layout | The harness in `src/rf_skill_eval/` and the ADRs |
| 2026-04-27 | [claude-code-extension-quality-evaluation.md](claude-code-extension-quality-evaluation.md) | Metrics for judging Claude Code extensions | ADR-003 and ADR-004 |
| 2026-04-27 | [ddd-design.md](ddd-design.md) | Draft module layout of the harness | The ADRs in `docs/ci/architecture/adr/` |
| 2026-04-28 | [hooks-fix-proposal.md](hooks-fix-proposal.md) | Diagnosis of the plugin hooks | `plugins/rf-core/hooks/` and its README |
| 2026-05-07 | [installer-proposal.md](installer-proposal.md) | Proposal for the package and installer (was `docs/installer/proposal.md`) | `installer/` and its README |
| 2026-05-08 | [docker-test-harness-proposal.md](docker-test-harness-proposal.md) | Proposal for a Docker test harness of the installer | Nothing: the harness was removed in 2026-11 (change `repo-cleanup`); the installer tests use fake agent CLIs |
| 2026-05-13 | [issues/](issues/) | Windows PowerShell install and startup errors: raw logs and fix proposals | The fixes in `installer/` (see `installer/CHANGELOG.md`) |
| 2026-06-18 | [RF_AGENTSKILLS_ISSUE_REPORT.md](RF_AGENTSKILLS_ISSUE_REPORT.md) | Issue report on `rf-agentskills` for its maintainer | The fixes in the later releases |
