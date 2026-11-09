# Changelog

The `rf-api` plugin, versioned on its own (`rf-api--v<version>` tags); see `RELEASING.md` at the repository root.

## 1.0.0 (unreleased)

First release, split out of `rf-agentskills` 3.0.0: `rf-requests` and `rf-restinstance`. It depends on `rf-core` `^1.0`. Skill names are unchanged; their plugin prefix is now `rf-api:` instead of `rf-agentskills:`, for example `/rf-api:rf-requests`.

- **Install steps moved here** from `rf-setup`: `rf-requests` and `rf-restinstance` each have `references/install.md`. `rf-restinstance` also has `references/migrate-from-requests.md`, the RequestsLibrary → RESTinstance keyword map that `rf-migration-guide` used to carry.
