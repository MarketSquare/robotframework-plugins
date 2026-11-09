## MODIFIED Requirements

### Requirement: Distribution tooling rejects orphaned copies

Every distribution channel SHALL be built from the plugin's own `plugins/<name>/` tree: the installer's bundled assets, the release tarballs and the Claude Desktop ZIPs. A build SHALL contain no skill directory, subagent or helper script that the plugin tree does not have. The drift check SHALL fail when a generated Codex or OpenCode variant is missing, stale, or has no source subagent.

#### Scenario: Sync removes a retired skill's copies
- **WHEN** a skill directory is deleted from `plugins/<plugin>/skills/` and the installer and release packages are built
- **THEN** none of them contains that skill or its scripts

#### Scenario: Drift check catches an orphan
- **WHEN** a Codex or OpenCode variant exists for a subagent the plugin no longer ships
- **THEN** `scripts/check-drift.sh` exits non-zero and names the orphan

### Requirement: Retirements are released as a breaking content change

Removing a skill, a subagent or an MCP tool from a plugin SHALL bump that plugin's major version in its `plugin.json`, and SHALL be recorded in the plugin's CHANGELOG and in the release notes of the next installer release, with what was removed, why, and what to use instead.

#### Scenario: Version and changelog reflect the retirement
- **WHEN** the release containing a retirement is prepared
- **THEN** `plugins/<name>/.claude-plugin/plugin.json` carries a new major version and the marketplace entry carries no version
- **AND** the plugin's CHANGELOG entry lists the removed items and their replacements
