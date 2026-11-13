## ADDED Requirements

### Requirement: Libraries name the skills that cover them

Each entry of a manifest's `libraries` MAY have `skills`: a non-empty list of distinct skill names (kebab-case) of the same plugin that cover that library. When `skills` is absent, every skill of the plugin covers the library. The manifest schema SHALL accept `skills` and SHALL keep rejecting other unknown keys of a library entry. The catalogue check SHALL fail when a listed skill has no `plugins/<plugin>/skills/<skill>/SKILL.md`, naming the plugin, the library and the skill. The generated `docs/catalog.md` SHALL show the skills next to each library that names them, and the installer's bundled catalogue (`catalog.json`, `bundle.catalog()` and `bundle.fetch()` snapshots) SHALL carry `skills` unchanged. Every technology plugin of this repository SHALL name the skills of each of its libraries.

#### Scenario: Skills per library accepted
- **WHEN** `plugins/rf-web/catalog.yaml` lists Browser with `skills: [rf-browser]` and SeleniumLibrary with `skills: [rf-selenium]`
- **THEN** schema validation and the catalogue check pass

#### Scenario: Other unknown keys still rejected
- **WHEN** a library entry has a key `skill: rf-browser` (singular)
- **THEN** schema validation fails on that key

#### Scenario: Missing skill reported
- **WHEN** rf-api lists RequestsLibrary with `skills: [rf-requests-auth]` and `plugins/rf-api/skills/rf-requests-auth/SKILL.md` doesn't exist
- **THEN** the catalogue check fails with a message naming `rf-api`, `RequestsLibrary` and `rf-requests-auth`

#### Scenario: Passed through to tools
- **WHEN** a tool reads the `rf-web` entry of `bundle.catalog()`
- **THEN** its Browser library has `skills == ["rf-browser"]` and its SeleniumLibrary library has `skills == ["rf-selenium"]`

#### Scenario: Absent field keeps working
- **WHEN** a community plugin's manifest lists a library without `skills`
- **THEN** validation passes, and its catalogue entry has no `skills` key for that library
