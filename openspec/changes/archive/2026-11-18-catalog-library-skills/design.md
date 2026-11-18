## Context

See proposal.md (Why). What the change builds on:

- `schemas/catalog.schema.json` describes `libraries` items with `additionalProperties: false` and the keys `name`, `package` and `versions`. `scripts/build-catalog.py` validates every `plugins/<name>/catalog.yaml` against it, runs its own checks (`name_problems`, `symlink_problems`, `bundle_problems`, lifecycle and renames), and writes the README table, `docs/catalog.md` and the marketplace.
- The installer's `_catalog.py` (#5) copies `libraries` as it is into `catalog.json`. `bundle.catalog()` and `bundle.fetch()` read that, so a new key in a library entry reaches them with no installer code change.
- `rf-agentskills` is a bundle with `libraries: []`. A removed plugin keeps its manifest but leaves the catalogue.

## Goals / Non-Goals

**Goals:**
- One authoritative mapping from a library to the skills that cover it, checked against the skills on disk.
- No change for readers and community plugins that don't use the field.

**Non-Goals:**
- Per-skill installs in the installer.
- Pointing a library at another plugin's skill. Skills are named within their own plugin, because the plugin is the unit a user installs.
- A `CATALOG_FORMAT` bump: the field is optional and new.

## Decisions

### D1. Optional, same-plugin skill names

`skills` is optional, has at least one item, holds unique kebab-case names, and names skill folders of the same plugin. Absent means "every skill of the plugin", the only assumption a reader can make today, so existing catalogues keep their meaning. An empty list is rejected by `minItems: 1`: "no skill covers this library" would mean the library doesn't belong in the plugin's `libraries`.

Alternative: a top-level `skills` map (`{skill: [library]}`). It would need a second lookup and would let a library go unmapped silently; per-library keeps the answer next to the package a tool detected.

### D2. The check lives with the other catalogue checks

A new `library_skill_problems(plugins)` in `build-catalog.py` runs for every manifest (active, deprecated and removed alike, so a stale entry is caught before a plugin is revived). For each library and each listed skill, it reports `<plugin>: library <name> lists skill <skill>, but plugins/<plugin>/skills/<skill>/SKILL.md doesn't exist`. It runs in both `build-catalog.py` and `--check`, like `name_problems`.

### D3. Where the field shows

- `docs/catalog.md`: the library line becomes `Browser (robotframework-browser >=20,<21): rf-browser`.
- The README table keeps library names only: it is a summary and has no room.
- The marketplace has no field for it.

### D4. Installer: tests and docs only

No code change. The tests assert the field in `bundle.catalog()` (from the dev bundle) and in a `fetch()` snapshot (from the fake GitHub's archive). The README's "Python API" table lists `skills` among the library fields, with the "absent means every skill" rule. The changelog gets a line in the unreleased 2026.11.0 entry, next to the catalogue's `format` and `robotframework` additions.

## Risks / Trade-offs

- [A plugin adds a skill for a library and forgets `skills`] → The library keeps its old, narrower list, and tools miss the new skill. The check can't know intent; CONTRIBUTING.md asks plugin authors to update `skills` when they add or rename a skill. A rename that removes the old folder fails the check.
- [Community plugins never fill it in] → Readers fall back to all of the plugin's skills, which is today's behaviour.
