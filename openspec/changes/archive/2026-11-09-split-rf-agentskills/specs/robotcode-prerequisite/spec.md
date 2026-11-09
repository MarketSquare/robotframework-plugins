## MODIFIED Requirements

### Requirement: No plugin dependency on the robotcode plugin

The manifests of the Robot Framework plugins in this marketplace SHALL NOT declare a dependency on a plugin outside this marketplace:
- a Claude Code `plugin.json` MAY list `dependencies` only by bare name, which resolves in this marketplace (the technology plugins on `rf-core`, the `rf-agentskills` bundle on the five plugins); it SHALL NOT name a `marketplace` or use the `name@marketplace` form;
- no `dependencies` entry SHALL name `robotcode`;
- the marketplace SHALL NOT contain `allowCrossMarketplaceDependenciesOn`;
- the Codex, Copilot and Open Plugins manifests SHALL NOT contain an equivalent field that points outside this marketplace.

Installing any of these plugins SHALL succeed and load whether or not the robotcode plugin or its marketplace is present.

#### Scenario: Manifests carry no dependency
- **WHEN** every `plugin.json` and `marketplace.json` in the repository is parsed
- **THEN** no `dependencies` entry names a marketplace or `robotcode`, every one names a plugin of this marketplace, and no file has an `allowCrossMarketplaceDependenciesOn` key

#### Scenario: Plugin loads without the robotcode plugin
- **WHEN** `rf-core` is installed in Claude Code in an isolated home where the `robotframework-agent-plugins` marketplace was never added
- **THEN** the install succeeds and its skills, subagents and hooks are listed
