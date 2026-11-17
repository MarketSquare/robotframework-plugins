## MODIFIED Requirements

### Requirement: Paired treatment and baseline arms

The harness SHALL support two arms for every task. `treatment` provisions the plugin content as shipped: the skills, hooks and subagents of the repository's content plugins, merged the way the `rf-agentskills` bundle ships them. `baseline` provisions none of these. Apart from that, both arms SHALL use the same fixture, prompt, model, allowed tools, turn and time limits, and MCP servers (the per-task servers, such as `rf-mcp`). The baseline arm SHALL NOT be able to discover any of the repository's skills, whether user-level, project-level (`.claude/skills/`) or plugin-provided.

#### Scenario: Baseline run has no skills available
- **WHEN** a task runs in the `baseline` arm
- **THEN** the session's isolated config dir and workspace contain no skill, hook or subagent from the repository's plugins
- **AND** the transcript contains no successful load of one of the repository's skills

#### Scenario: Arms differ only by the plugin
- **WHEN** the same task runs in `treatment` and `baseline`
- **THEN** both runs use identical prompt, model, `max_turns`, `timeout_seconds`, allowed tools, fixture contents and MCP configuration
- **AND** the run records store the arm name

#### Scenario: Selecting arms on the command line
- **WHEN** a batch is started with `--arms treatment,baseline`
- **THEN** every selected task runs in both arms
- **WHEN** a batch is started without `--arms`
- **THEN** only the `treatment` arm runs
