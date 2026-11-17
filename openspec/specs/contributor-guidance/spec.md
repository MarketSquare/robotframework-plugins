# contributor-guidance Specification

## Purpose
What people and coding agents need to contribute here: the AI contribution policy (`AI_POLICY.md`), the agent guide (`AGENTS.md`) checked against CI, the RobotCode-first rule, the AI and RobotCode items in the templates, and the OpenSpec project context.

## Requirements

### Requirement: AI contribution policy

The repository SHALL contain `AI_POLICY.md`, linked from `README.md`, `CONTRIBUTING.md` and `AGENTS.md`. It SHALL state that:
- AI tools and coding agents are welcome, and the human who submits a contribution is responsible for it: they understand it, have reviewed all generated output, have run the documented checks, and handle review feedback themselves;
- a pull request, issue or comment made with substantial AI help says so where reviewers see it, with an optional `AI-Assisted-By: <tool>` commit trailer; grammar fixes, formatting and ordinary editor completions need no disclosure;
- by submitting, the contributor confirms the right to submit the content under the Apache-2.0 licence, and that generated content with unclear origin or copied third-party material is disclosed or left out;
- skills, hooks, subagents and scripts are read and run by other people's agents, so changes to them are security-relevant and go through the security gate;
- every keyword a skill teaches resolves against the library it names, as `scripts/check-skill-keywords.py` checks;
- generated files (`bundles/`, `docs/catalog.md`, `.claude-plugin/marketplace.json`, `plugins/*/variants/`, eval baselines) are never edited by hand, and a change to them names the command that regenerated them;
- paid live eval runs and re-baselines are dispatched by maintainers;
- eval tasks and fixtures read like real user requests and real projects, and don't hint at the grading;
- low-context, fully automated or unverified submissions may be closed, and maintainers decide how the policy applies.

#### Scenario: Disclosure asked for
- **WHEN** a contributor opens a PR whose code an agent wrote
- **THEN** the PR template asks for the disclosure, and `AI_POLICY.md` says what it confirms

#### Scenario: Generated file edited by hand
- **WHEN** a contributor asks an agent that follows `AGENTS.md` to change a skill that the bundle copies
- **THEN** the guide tells it to edit `plugins/<name>/` and run `python scripts/build-catalog.py`, not to edit `bundles/`

### Requirement: RobotCode is the base of the Robot Framework AI toolstack

`AI_POLICY.md` and `AGENTS.md` SHALL state the RobotCode-first rule:
- the `robotcode` CLI (https://robotcode.io/guides/cli/) is the core of the Robot Framework AI toolstack;
- AI solutions in this repository use it for running tests, discovery, static analysis, result analysis, running keywords step by step in the REPL, keyword and library documentation, and debugging, in preference to new custom implementations of those capabilities;
- a capability RobotCode lacks is reported or contributed upstream to RobotCode, the central place for such improvements, rather than worked around here;
- custom scripts (hook glue, skill helpers, eval grading, project conventions) are welcome when they call `robotcode` for these capabilities instead of re-implementing them.

`AGENTS.md` SHALL contain a capability map that names, for each capability, the `robotcode` command and the guide page that documents it: `robot`/`run`, `discover`, `analyze code`, `results`, `repl`, `robot-debug`, `doc`, `--wrapper`, and `config`/`profiles`.

#### Scenario: Agent needs keyword documentation
- **WHEN** an agent working on a skill needs the arguments of a library keyword
- **THEN** `AGENTS.md` points it to `robotcode doc keyword`, not to a custom libdoc script

#### Scenario: Missing capability
- **WHEN** a contributor finds that `robotcode` can't do something a skill needs
- **THEN** the policy tells them to open an issue or PR at RobotCode, and a custom script for it states in a comment which upstream issue it covers

### Requirement: Agent guide matches CI

The repository SHALL contain `AGENTS.md` with the layout, the local checks, the generated files with their regenerate commands, the files never to commit, and the OpenSpec workflow. `CLAUDE.md` SHALL consist of an import of `AGENTS.md`, so both agents read one text. A repository test SHALL fail when:
- `AGENTS.md`, `AI_POLICY.md` or `CLAUDE.md` is missing;
- a `scripts/…` path named in `AGENTS.md` doesn't exist;
- a check command listed in the "Checks" section of `AGENTS.md` doesn't appear in `.github/workflows/ci.yml`;
- `CLAUDE.md` doesn't import `AGENTS.md`.

`AGENTS.md`, `AI_POLICY.md` and `CLAUDE.md` SHALL pass the docs voice check.

#### Scenario: Script renamed
- **WHEN** a PR renames `scripts/check-drift.sh` and doesn't update `AGENTS.md`
- **THEN** the repository test fails and names the missing path

#### Scenario: Check dropped from CI
- **WHEN** a PR removes `python scripts/check-docs-voice.py` from `ci.yml` but `AGENTS.md` still lists it
- **THEN** the repository test fails and names the command

### Requirement: PR template asks about AI use and RobotCode

`.github/pull_request_template.md` SHALL have an "AI assistance" section that asks for the disclosure or "none", and a checklist item stating that Robot Framework capabilities go through `robotcode` and that gaps are reported upstream. The issue template SHALL ask reporters to disclose AI-generated reports. A repository test SHALL check that both are present.

#### Scenario: Template item removed
- **WHEN** a PR deletes the RobotCode item from the PR template
- **THEN** the repository test fails

### Requirement: OpenSpec proposals get project context

`openspec/config.yaml` SHALL set `context` with the project summary (marketplace plugins, the installer, the eval harness, security scanning), the layout, the RobotCode-first rule and the docs voice. It SHALL also set `rules`:
- a proposal that touches a Robot Framework capability names the `robotcode` command it uses, or says why none fits;
- every task has a verify clause.

#### Scenario: Proposal drafted by an agent
- **WHEN** an agent runs `openspec instructions proposal` for a new change
- **THEN** the returned context contains the RobotCode-first rule and the proposal rule
