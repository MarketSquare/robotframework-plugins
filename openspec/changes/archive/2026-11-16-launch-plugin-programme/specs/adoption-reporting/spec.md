## Purpose

Defines how the programme learns which plugins deliver value, using public signals and voluntary feedback only, without collecting data from the machines where plugins and the installer run.

## ADDED Requirements

### Requirement: No telemetry

The installer, hooks and scripts SHALL NOT send usage data, identifiers or content to any service. The only network access the installer makes on its own SHALL be the marketplace and package operations the user requested. `SECURITY.md` and the README SHALL state this.

#### Scenario: Install makes no reporting call
- **WHEN** `robotframework-plugins install --agent claude-code --yes` runs with network traffic recorded
- **THEN** no request goes to any host other than those needed for the requested install

### Requirement: Public adoption signals are collected

A scheduled workflow SHALL collect, at least weekly, the GitHub traffic data for the repository (views, clones, referrers), which GitHub keeps for only 14 days, and SHALL store it in the repository on a dedicated data branch. The quarterly report SHALL also use PyPI download counts for `robotframework-plugins`, issue and discussion counts per plugin label, and eval scores from the committed baselines.

#### Scenario: Traffic is not lost
- **WHEN** the collection workflow has run every week for a quarter
- **THEN** the data branch holds daily view and clone counts for every day of that quarter

### Requirement: Users can give feedback per plugin

The repository SHALL provide an issue form for plugin feedback that asks for the plugin, the agent and model used, the Robot Framework and library versions, and whether the plugin helped. Issues from the form SHALL be labelled with the plugin name.

#### Scenario: Feedback is labelled
- **WHEN** a user submits the feedback form for `rf-agentskills`
- **THEN** the new issue carries the `plugin:rf-agentskills` label

### Requirement: Quarterly adoption report

Each quarter, the programme SHALL publish `docs/reports/adoption-<YYYY>-Q<n>.md`, generated from the collected signals. It SHALL show, per plugin, downloads, feedback issues (positive and negative), open issues, eval scores and their trend, and SHALL list plugins that are candidates for promotion, demotion or deprecation.

#### Scenario: Report names candidates
- **WHEN** a verified plugin's eval score fell for two releases
- **THEN** the report lists it as a demotion candidate
