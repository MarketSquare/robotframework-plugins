## MODIFIED Requirements

### Requirement: The bundle ships no MCP server

No plugin SHALL ship an MCP server or an MCP server configuration in any channel: no plugin has a `.mcp.json` or a `servers/` directory, and the installer writes no MCP server entry for any agent. Skills SHALL run their helper scripts or the project's robotcode CLI directly. Shipped content SHALL NOT instruct the agent to call `rf_libdoc_search`, `rf_libdoc_explain`, `rf_results_analyze` or `rf_check_library`.

#### Scenario: Plugin has no MCP config
- **WHEN** every plugin tree under `plugins/` is listed
- **THEN** none contains a `.mcp.json` or a `servers/` directory

#### Scenario: Subagents name skills, not tools
- **WHEN** the subagent files are searched for the retired tool names
- **THEN** none is found, and keyword lookup and results reading use `robotcode doc` and `robotcode results`
