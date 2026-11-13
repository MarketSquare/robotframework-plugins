# Changelog

The `rf-desktop` plugin, versioned on its own (`rf-desktop--v<version>` tags); see `RELEASING.md` at the repository root.

## 1.0.0 (unreleased)

First release, split out of `rf-agentskills` 3.0.0: `rf-platynui`. It depends on `rf-core` `^1.0`. Skill names are unchanged; their plugin prefix is now `rf-desktop:` instead of `rf-agentskills:`, for example `/rf-desktop:rf-platynui`.

- **Install steps moved here** from `rf-setup`: `rf-platynui` has `references/install.md`, with the pre-release pin.
- **`rf-platynui` names `robotcode doc keyword PlatynUI.BareMetal "<Keyword>"`** in its Library Import section, as the way to check a keyword and its arguments.
