## MODIFIED Requirements

### Requirement: The old PyPI package forwards to the new one

The final `rf-agentskills` release on PyPI, `0.9.0`, SHALL depend on `robotframework-plugins>=5.0.0`, the first release under the shared version, because the calendar versions before it are yanked. It SHALL provide an `rf-agentskills` command that prints a one-line deprecation notice to stderr and then runs `robotframework-plugins` with the same arguments and exit code, and SHALL say in its PyPI description that the project has moved. No later `rf-agentskills` release SHALL be made.

#### Scenario: Old command keeps working
- **WHEN** a user runs `uvx rf-agentskills install --agent claude-code --yes`
- **THEN** stderr shows the deprecation notice naming `robotframework-plugins`, and the install completes as it would with `uvx robotframework-plugins install --agent claude-code --yes`
