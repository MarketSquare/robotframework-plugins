## Why

The catalogue maps a library to a plugin, but a plugin can ship several skills for different libraries (rf-web: Browser and SeleniumLibrary; rf-api: RequestsLibrary and RESTinstance). A tool that detects one library can't tell which skill covers it ([issue #7](https://github.com/MarketSquare/robotframework-plugins/issues/7)).

rf-mcp reads the catalogue through `bundle.catalog()` (#5) to attach skills to an agent's first tool call. In its evaluation at `37562367`, a Browser project that also had RequestsLibrary installed got `rf-requests`, `rf-restinstance` and `rf-browser`, in that order. rf-mcp now guesses the skill from its name (Browser → `rf-browser`). That's a naming convention, not a contract: a skill such as `rf-api-auth` or a company plugin breaks it.

## What Changes

- **Schema:** `libraries[].skills`, an optional list of skill names of the same plugin that cover the library, in `schemas/catalog.schema.json`. Other unknown keys stay rejected.
- **Check:** `scripts/build-catalog.py --check` fails when a listed skill has no `plugins/<plugin>/skills/<skill>/SKILL.md`, naming the plugin, the library and the skill.
- **Data:** the four technology plugins name their skills per library:
  - rf-web: Browser → `rf-browser`, SeleniumLibrary → `rf-selenium`;
  - rf-api: RequestsLibrary → `rf-requests`, RESTinstance → `rf-restinstance`;
  - rf-mobile: AppiumLibrary → `rf-appium`;
  - rf-desktop: PlatynUI → `rf-platynui`.
- **Output:**
  - `catalog.json` in the installer wheel, `bundle.catalog()` and `bundle.fetch()` snapshots carry the field unchanged;
  - `docs/catalog.md` lists the skills next to each library.
- **Docs:** CONTRIBUTING.md (the `catalog.yaml` step) and the installer README's "Python API" table explain the field: when it's absent, every skill of the plugin covers the library.

The field is optional and new, so `CATALOG_FORMAT` stays `1`, and catalogues and readers without it keep working.

Out of scope: per-skill installs (`install` picking `rf-browser` without `rf-selenium`). The issue mentions that the installer could use the field; that would be a separate change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `plugin-catalogue`: the programme manifest's `libraries` entries may name the skills that cover them, the catalogue check verifies those skills exist, and the generated catalogue and the installer's catalogue pass them on. (The capability is added by the unarchived change `launch-plugin-programme`; this change adds a requirement to it.)

## Impact

- **Schema and tooling:** `schemas/catalog.schema.json`, `scripts/build-catalog.py` (check and `docs/catalog.md`), `tests/test_catalog.py`.
- **Data:** `plugins/rf-web/catalog.yaml`, `plugins/rf-api/catalog.yaml`, `plugins/rf-mobile/catalog.yaml`, `plugins/rf-desktop/catalog.yaml`; regenerated `docs/catalog.md`.
- **Installer:** no code change, because `_catalog.py` already passes `libraries` through. Tests for `bundle.catalog()` and snapshots, the README "Python API" table, and a changelog line for 2026.11.0, which is still unreleased.
- **Docs:** `CONTRIBUTING.md`.
- **Consumers:** rf-mcp can map a detected package to its skill without guessing and fall back to all of a plugin's skills when `skills` is absent.
