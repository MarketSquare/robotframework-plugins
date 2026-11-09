# Changelog

The `rf-web` plugin, versioned on its own (`rf-web--v<version>` tags); see `RELEASING.md` at the repository root.

## 1.0.0 (unreleased)

First release, split out of `rf-agentskills` 3.0.0: `rf-browser` and `rf-selenium`. It depends on `rf-core` `^1.0`. Skill names are unchanged; their plugin prefix is now `rf-web:` instead of `rf-agentskills:`, for example `/rf-web:rf-browser`.

- **Install steps moved here** from `rf-setup`: `rf-browser` and `rf-selenium` each have `references/install.md`, with the full post-install steps, verification, troubleshooting and the CI step. `rf-browser` also has `references/migrate-from-selenium.md`, the SeleniumLibrary → Browser keyword map that `rf-migration-guide` used to carry.
