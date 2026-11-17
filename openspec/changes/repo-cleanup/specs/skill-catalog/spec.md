## MODIFIED Requirements

### Requirement: Generator skills are not shipped in any remaining channel

The content SHALL NOT contain the skills `rf-keyword-builder`, `rf-testcase-builder` or `rf-resource-architect`, nor the scripts `keyword_builder.py`, `testcase_builder.py` or `resource_architect.py`, in any channel: the plugins under `plugins/` (the source of every marketplace install), the `bundles/rf-agentskills` copy, the installer's bundled assets, or the release tarballs built from them.

#### Scenario: No generator skill directories in any channel
- **WHEN** `plugins/*/skills/`, `bundles/rf-agentskills/skills/` and a freshly built installer `_assets/` tree are listed
- **THEN** none contains a skill whose `name:` or directory is `rf-keyword-builder`, `keyword-builder`, `rf-testcase-builder`, `testcase-builder`, `rf-resource-architect` or `resource-architect`

#### Scenario: No generator scripts shipped
- **WHEN** the plugin and bundle `scripts/` directories, the skill `scripts/` directories and the installer `_assets/` tree are listed
- **THEN** none contains `keyword_builder.py`, `testcase_builder.py` or `resource_architect.py`
