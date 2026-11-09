## REMOVED Requirements

### Requirement: Setup skill is distributed without drift

**Reason**: Root `skills/` and the sync step are removed; each plugin's `plugins/<name>/skills/` is the only source (`plugin-catalogue`, "Each plugin owns its sources, tests and evals").

**Migration**: Edit the skill under `plugins/<plugin>/skills/`. The drift check now covers only the generated Codex and OpenCode variants.
