## Context

`launch-plugin-programme` moves `rf-agentskills` 3.0.0 into `MarketSquare/robotframework-plugins` and gives every plugin its own sources, tests, evals, version and tags (its D3 and D13). This change starts from that layout, after that change's task groups 1–3, and before its first release.

What the plugin contains today, and what ties it to specific libraries:

| Part | Size | Tied to a library? |
|---|---|---|
| `rf-language` | 240K | no |
| `rf-python-library` | 152K | no |
| `rf-setup` | 96K | yes: a row and post-install steps for every library |
| `rf-browser`, `rf-selenium` | 76K, 68K | web |
| `rf-requests`, `rf-restinstance` | 64K each | API |
| `rf-appium` | 80K | mobile |
| `rf-platynui` | 72K | desktop |
| 3 subagents (94–102 lines) | | by name: each routes to all 9 skills; `rf-migration-guide` holds SeleniumLibrary→Browser and RequestsLibrary→RESTinstance tables |
| hooks: validate, error hints, pending errors, test reminder, project validation | | no |
| hook: context injection | | names all 9 skills in its regex and text |
| hook: `SessionStart` environment check | | probes each library's import |
| MCP | none | the `skill-catalog` spec forbids shipping one |

Only `rf-language` and `rf-python-library` ship Python scripts, and both go to core. The installer's file mode puts each plugin's scripts and hooks in `<root>/rf-agentskills-files/` (Claude Code, Codex, Cursor, OpenCode).

Claude Code facts this design relies on (code.claude.com plugin docs, read 2026-11-08):
- `plugin.json` `dependencies` installs other plugins, with semver ranges resolved against `<plugin>--v<version>` tags. A plugin with only a `name` and `dependencies` is a valid bundle.
- A symlink in a plugin that points elsewhere in the same marketplace is copied as its target's content.
- There is no deprecation state, and `relevance` suggestions appear only for marketplaces an admin allowlists.

Not known yet: whether Copilot CLI and Codex resolve `dependencies`, and whether symlinks survive a Windows checkout with `core.symlinks=false`.

## Goals / Non-Goals

**Goals:**
- A web, API, mobile or desktop team installs core plus their technology and nothing else.
- Every existing install keeps every skill after the upgrade, with no action needed.
- A new technology plugin needs no PR against `rf-core`.
- Core never sends the agent to a skill that may not be there.

**Non-Goals:**
- Database, Java or Windows-only plugins. They come with content and a maintainer group, under the programme's rules.
- Rewriting skill content beyond moving the install steps and migration tables.
- Making robotcode's own plugin a dependency of `rf-core` (see D9).
- Splitting the hooks across plugins.

## Decisions

### D1 Split by technology, with core holding Robot Framework itself
```
              rf-agentskills 4.0.0 (bundle, no content)
                |       |        |          |
                v       v        v          v
             rf-web  rf-api  rf-mobile  rf-desktop      each 1.0.0
                \       |        |        /
                 v      v        v       v
                       rf-core 1.0.0
     rf-language  rf-setup  rf-python-library
     rf-test-architect  rf-debug-expert  rf-migration-guide
     all hooks
```
- **Why technology, not one plugin per library:** users pick by what they test, and siblings that need each other's boundary text (Browser vs Selenium, Requests vs RESTinstance) stay together (`skill-triggering`, "Sibling skills share a plugin"). One plugin per library would mean 6 plugins, 6 version lines and 6 tags for 6 skills.
- **Ownership within a plugin** goes by path in CODEOWNERS, for example `plugins/rf-web/skills/rf-browser/` to the Browser maintainers. This replaces the wording of the launch change's D16; see D10.
- **`rf-python-library` stays in core.** It covers extending Robot Framework, not a technology, and most projects grow a Python keyword or a listener.
- **No empty plugins.** `rf-database` and the others are created when they have content and a maintainer.

### D2 Library installs move to the library skills
`rf-setup` keeps environments (uv, venv + pip, Poetry), Python floors, robotcode and Robocop, troubleshooting, and a one-row-per-library table: package, `uv add` command, a one-line post-install summary, and the owning skill and plugin. Full post-install steps move to `references/install.md` in each library skill.
- **Why:** a new technology plugin can then ship its install steps without a PR against `rf-core`, and the person who knows `rfbrowser install` maintains it.
- **The cost:** a table row in `rf-setup` per library is still a core change, but it is one line, and a test checks that its `uv add` command matches the library skill's. Generating the table from `catalog.yaml` would remove even that, but needs an install field in the manifest; it is left for later.
- *Rejected: keep everything in `rf-setup`.* Every technology would need core maintainers' review for install details they don't own.
- **Re-measure:** this changes the "Not installs: rf-setup" routing, so the trigger and narrow evals of `rf-setup` and the library skills are re-run (task 6).

### D3 Core routes generically and names plugins
- **Context injection hook:** keeps the library names in its trigger regex (a Browser question is still a Robot Framework question), but its text says "use the library's own skill; if none is loaded, suggest installing `rf-web` / `rf-api` / `rf-mobile` / `rf-desktop`". It names only `rf-core` skills. This fits the 450-character budget.
- **Subagents:** library routes become "`rf-browser` (plugin `rf-web`)", plus one line telling the subagent to suggest the plugin when the skill is missing.
- **A lint** checks every file in a plugin: a skill name from another plugin needs that plugin's name nearby, on the same line or in the same table row.
- **Environment check:** stays in core and keeps probing imports. For each library it finds, it names the plugin once and gives the install command for that agent. This is the discovery path that works on every agent, unlike `relevance`.
- *Rejected: each technology plugin ships its own context hook.* That means more processes per prompt and four copies of the trigger logic, for routing that the skill descriptions already handle.

### D4 Migration tables move to the target library
SeleniumLibrary→Browser goes to `rf-browser/references/migrate-from-selenium.md`, and RequestsLibrary→RESTinstance goes to `rf-restinstance/references/migrate-from-requests.md`. `rf-migration-guide` keeps the Robot Framework version and syntax migrations and the phased method, and routes library moves to the target skill. Both tables are already marked agent-owned, so the move changes no content.

### D5 The bundle and dependencies, decided by a spike
The spike (task 1) installs a test marketplace with a bundle and a dependency on Copilot CLI and Codex, and checks out a symlink on Windows with `core.symlinks=false`.

| Spike result | Bundle `rf-agentskills` | Shared files (launch D15) |
|---|---|---|
| Copilot and Codex resolve `dependencies` | `dependencies` only | symlinks, if Windows keeps them |
| They don't, Windows keeps symlinks | `dependencies`, plus `skills/` and `agents/` symlinked to the five plugins; hooks referenced from `rf-core` | symlinks |
| They don't, Windows breaks symlinks | `dependencies`, plus real copies generated at build time into the bundle and checked by the drift check | generated copies, checked by the drift check |

- **When copies are used,** the bundle loads the same skill names as the plugins it depends on. On Claude Code, which resolves `dependencies`, the bundle then ships no copies and relies on dependencies. If the spike shows that one marketplace can't serve both behaviours, the fallback is a documented note: Codex and Copilot users install the five plugins, and the installer does it for them.
- **Why `dependencies` first:** it is the documented mechanism, versions resolve by tag, and nothing is duplicated.

### D6 Installer selection follows the project, then the previous install
- **Fresh install:** `rf-core` plus the verified plugins whose library packages the project declares (`pyproject.toml` PEP 621, Poetry and dependency groups; `requirements*.txt`). If none are detected, every verified plugin is installed, as today.
- **Upgrade:** the plugins that cover what is already installed, so nothing disappears silently. Narrowing needs `--plugins`.
- **Where the library list comes from:** `catalog.yaml` `libraries` gains the PyPI package name per library, for example `robotframework-browser`. The launch change's schema already lists libraries; this adds `package`.
- *Rejected: always install everything.* It keeps the listing-budget and noise problem the split exists to fix.
- *Rejected: core only when nothing is detected.* A new project would start without the skill for the library it is about to choose; `rf-test-architect` would have to install plugins mid-design.

### D7 File-mode layout per plugin
`<root>/<plugin>-files/` replaces `<root>/rf-agentskills-files/`. Only `rf-core` has scripts and hooks today, so only `rf-core-files/` exists. Skill folders stay flat and unchanged (`.claude/skills/rf-browser/`), which launch D14's unique-name rule makes safe. The upgrade moves the old folder, rewrites hook commands and records each file under its plugin. It reuses the existing pruning that keeps user-modified files.

### D8 Versions
`rf-core`, `rf-web`, `rf-api`, `rf-mobile` and `rf-desktop` start at 1.0.0. The bundle `rf-agentskills` goes to 4.0.0, because skill prefixes change. Technology plugins depend on `rf-core` `^1.0`. All six are released together the first time, with one installer release whose version table lists them.

### D9 robotcode stays a prerequisite, not a dependency
A cross-marketplace dependency on robotcode's plugin would install another project's plugin automatically, and needs `allowCrossMarketplaceDependenciesOn`. That is a trust decision for the Foundation and the robotcode maintainers, not a packaging detail, so `robotcode[all]>=2.8` stays a documented prerequisite (`robotcode-prerequisite`).

### D10 Edits to `launch-plugin-programme`
- Its non-goal "Splitting `rf-agentskills`" is replaced by a pointer to this change.
- Its D16 becomes: "A plugin is the unit of installation; a skill folder is the unit of ownership, through CODEOWNERS paths."
- Task order: groups 1–3, then this change, then groups 4–10. Task 10.2 releases the plugins from this change, so `rf-agentskills--v3.1.0` is never released.
- Its spec deltas that name `rf-agentskills` as the only plugin are updated where they would be false after the split. Where the bundle keeps them true, they stay unchanged.

## Risks / Trade-offs

- **Skill prefixes change** (`rf-agentskills:rf-browser` → `rf-web:rf-browser`). Users who type the prefixed name see a different one, and docs or project instructions that name prefixed skills go stale. → Release notes and the bundle's changelog say so, and skill names without a prefix are unchanged.
- **The bundle works differently per agent** → the spike decides, and the bundle scenario in `plugin-split` is tested on Claude Code, Copilot CLI and Codex.
- **Detection picks too few plugins** for a project that adds a library later → the `SessionStart` report names the missing plugin, and `install --plugins` adds it.
- **Moving install steps changes routing** → trigger and narrow evals are re-run before release, against the 3.0.0 baselines.
- **More moving parts:** six `plugin.json` files, six changelogs and six tags → the catalogue generator writes the marketplace, and `bump-version.sh <plugin>` handles one plugin at a time.

## Migration Plan

1. In the new repository, after launch task groups 1–3: run the spike, then create the five plugin directories by `git mv` from `plugins/rf-agentskills/`, so history follows each file.
2. Move the install steps and migration tables, and update the hooks, subagents, lint, installer and evals.
3. Turn `plugins/rf-agentskills/` into the bundle.
4. Continue with launch groups 4–10. The first release ships the five plugins, the bundle and the installer together.

**Rollback:** before the first release, revert the split commits; launch task 10.2 then releases `rf-agentskills--v3.1.0` as originally planned. After release, a plugin can't be un-split without another breaking release, so the evals and agent checks in tasks 6 and 7 come first.

## Open Questions

- Who maintains each technology plugin at launch? A verified tier needs two maintainers per plugin (launch `plugin-trust-tiers`). If only one person maintains everything, the technology plugins start as `community` or the Foundation names co-maintainers.
- Do the Browser and SeleniumLibrary maintainers want to own their skill folders?
- Should `rf-desktop` later take Windows-only libraries such as FlaUI, or should they get their own plugin? This is decided when content exists.
