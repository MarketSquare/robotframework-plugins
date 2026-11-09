# Changelog

The `rf-core` plugin, versioned on its own (`rf-core--v<version>` tags); see `RELEASING.md` at the repository root.

## 1.0.0 (unreleased)

First release, split out of `rf-agentskills` 3.0.0: `rf-language`, `rf-setup` and `rf-python-library`, the `rf-test-architect`, `rf-debug-expert` and `rf-migration-guide` subagents, and all hooks. Skill names are unchanged; their plugin prefix is now `rf-core:` instead of `rf-agentskills:`, for example `/rf-core:rf-language`.

- **Library install steps moved to the library skills.** `rf-setup` keeps environments, uv, pip, Poetry, robotcode, Robocop and troubleshooting, and a table naming each library's package, install command, skill and plugin.
- **Library migration tables moved** to `rf-browser` (plugin `rf-web`) and `rf-restinstance` (plugin `rf-api`); `rf-migration-guide` routes library moves there.
- **Core names the plugin of every library skill**, and the subagents, hooks and `rf-setup` suggest installing the plugin when its skill is missing.
