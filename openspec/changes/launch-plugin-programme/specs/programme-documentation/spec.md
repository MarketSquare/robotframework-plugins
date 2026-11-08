## Purpose

Defines which documents the programme publishes and holds them to the Robot Framework Voice: friendly, versatile and effective, direct with dry humour, technically grounded and free of corporate filler.

## ADDED Requirements

### Requirement: Required documents

The repository SHALL contain:
- `README.md`: what the marketplace is, the generated catalogue, install per agent, the trust tiers in short, and links to the other documents;
- `CONTRIBUTING.md`: how to add or change a plugin, the checks a PR must pass, the writing rules, and a short section on the three kinds of version (plugin SemVer in `plugin.json`, installer CalVer, internal `rf-skill-eval`) that says plugin authors only ever bump their own plugin;
- `GOVERNANCE.md`: tiers, review, maintainer expectations and lifecycle;
- `SECURITY.md`: see `content-security-scanning`;
- `RELEASING.md`: plugin releases (`<plugin>--v<version>` tags) and installer releases (CalVer, `robotframework-plugins-v<version>` tags), the generated version table, and the PyPI publishing flow;
- `templates/plugin/`: a starter plugin with `catalog.yaml`, a README and one example skill that passes every check;
- the installer README published on PyPI.

#### Scenario: Template plugin passes CI
- **WHEN** CI copies `templates/plugin/` to `plugins/example/` in a scratch checkout and runs every PR check
- **THEN** all checks pass

### Requirement: Documents follow the Robot Framework Voice

Documents written for people SHALL:
- open with what the reader gets or can do, not with a mission statement;
- use short, modular sections with descriptive headings, and lists for steps and options;
- use inclusive, plain language and explain any jargon the first time it is used;
- keep humour dry and rare: never in install steps, error messages or security text;
- prefer action-driven statements over corporate phrasing.

CI SHALL fail when a document matches a banned-phrase list that includes "Our mission is", "leverage", "best-in-class", "seamless" and "world-class", and on more than one exclamation mark per document.

#### Scenario: Banned phrase
- **WHEN** a PR adds "Our mission is to empower testers" to `README.md`
- **THEN** the docs voice check fails and names the phrase and line

#### Scenario: Install steps stay plain
- **WHEN** a reviewer reads the README install section
- **THEN** it contains only commands and the facts needed to run them

### Requirement: Docs say what the checks cannot promise

The README and `SECURITY.md` SHALL state that passing the automated checks and the review does not prove a plugin is safe, and that a plugin's tier describes the evidence behind it, not a warranty.

#### Scenario: Limits stated
- **WHEN** a user reads the trust tiers section of the README
- **THEN** it says what `verified` means and what it does not guarantee

### Requirement: Contributors can tell which version to bump

`CONTRIBUTING.md` SHALL explain, in at most one screen, why a plugin and the installer have unrelated version numbers, with the version table as the example, and SHALL name the one command a plugin author runs to bump their plugin.

#### Scenario: Version question answered
- **WHEN** a contributor asks why the installer is `2026.12.0` and `rf-agentskills` is `3.1.0`
- **THEN** the "Versions" section of `CONTRIBUTING.md` answers it, and names `scripts/bump-version.sh <plugin> <major|minor|patch>`
