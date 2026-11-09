## Context

See proposal.md for why. The current state that shapes the approach:

- **Source:** `manykarim/robotframework-agentskills` `main` (`b1d5f82`, 2026-11-07), after its last releases: content `v3.0.0` and installer `rf-agentskills` 0.8.0.
  - One plugin, `rf-agentskills`: 9 skills, 3 subagents, hooks, and Codex and OpenCode variants.
  - An installer for 7 agents (PyPI `rf-agentskills` 0.8.0).
  - The internal `rf-skill-eval` harness with committed baselines on Haiku and Sonnet 5.5.
  - 23 OpenSpec main specs.
- **Released versions:** content `v3.0.0` (2.0.0 was never tagged; its changes shipped in 3.0.0) and installer `rf-agentskills-v0.8.0`. Tags to carry over: `v1.1.0`, `v1.2.0`, `v3.0.0` and `rf-agentskills-v0.3.0` to `rf-agentskills-v0.8.0`, including the release candidates.
- **Target:** `MarketSquare/robotframework-plugins`.
  - It has one commit, `8f24793`, containing an Apache-2.0 `LICENSE` identical to the source's and a GitHub-template Python `.gitignore` that differs from the source's.
  - The user has admin rights.
  - The PyPI name `robotframework-plugins` is free.
- **Planning base:** this change was drafted on the branch `plan/robotframework-plugins-programme`, seeded with `openspec/config.yaml` and `openspec/specs/` from the source's `main`. The change itself is the only new content.
- **Scanner spike** (2026-11-07). Tools at pinned versions without model passes, run on the real plugin and on a copy with 7 planted, inert attacks:
  - SkillSpector 2.13.4 and Cisco skill-scanner 2.3.2 between them caught every planted text and script attack, including one in a subagent. cc-audit 3.23.37 caught only the shipped `.mcp.json` with `npx …@latest`.
  - On clean content, SkillSpector raised 30 findings in 134 s and Cisco raised 7 in 11 s. None was a real issue. With `--lenient` over the whole plugin, Cisco flagged every hook script as CRITICAL for using `child_process`.
  - The secrets canary was inconclusive: the fake key had the wrong length for Gitleaks' Anthropic rule.
- **Single-plugin assumptions in the source:**
  - Root `skills/` is the canonical skill source. `scripts/sync-skills.sh` copies it into `plugins/rf-agentskills/skills/`, `scripts/check-drift.sh` checks the copy, and `release.yml` builds the skills tarballs from the root copy.
  - One repository-wide content version: `VERSION`, written by `scripts/bump-version.sh` into `marketplace.json` (`metadata.version` and the entry), `plugin.json` and every `SKILL.md` `metadata.version`. Setting the version in both the entry and `plugin.json` is what Claude Code's docs advise against; `plugin.json` silently wins.
  - Repository-wide `v*` release tags, and `tests/` and `eval/` written for one plugin.
  - The installer's file mode copies skills into one flat folder per agent (for example `.claude/skills/<name>`), so two plugins with a skill of the same name would overwrite each other.
- **Content-rule check:** `rf-agentskills` passes every proposed house content rule except one: `rf-test-architect` and `rf-migration-guide` declare no `tools` list, so they inherit every tool.

## Goals / Non-Goals

**Goals:**
- One merge-based copy that keeps blame, authorship and tags.
- A programme a contributor can follow without asking: manifest, checks, review, tier, lifecycle.
- A PR gate that is safe to run on fork PRs and quiet on content that has already been reviewed.
- Existing users keep working until they switch, and switching is one command.

**Non-Goals:**
- Splitting `rf-agentskills` into several plugins. That is the separate change `split-rf-agentskills`, applied between this change's task groups 3 and 4; see the Migration Plan.
- Plugins whose source lives in other repositories (Option B). Not now. The marketplace format already supports it: a `github` or `git-subdir` source pinned to a reviewed `sha`. That is the route for a later restructure, with the plugin's `catalog.yaml`, baseline and CODEOWNERS entry staying in this repository next to the pin.
- A hosted catalogue website. The generated README table and `docs/catalog.md` come first.
- Signing plugins or attesting their provenance beyond PyPI trusted publishing.
- Rewriting skill content, apart from the explicit `tools` lists required by the house rules.

## Decisions

### D1 Copy by merging unrelated histories, not by transfer or snapshot
Push the source `main` to a branch in the target, then merge it into the target `main` with `--allow-unrelated-histories`. Resolve the only conflict, `.gitignore`, by keeping the source version, and keep the identical `LICENSE`. Push the tags listed in Context unchanged.
- *Rejected: GitHub repository transfer.* The target already exists under the name we want, and you asked for a copy. A transfer would also move issues, which we don't need.
- *Rejected: a single snapshot commit.* It loses `git blame` and authorship, which matter for a community programme.

### D2 What is renamed
Exactly the map in `repository-migration`. The plugin name `rf-agentskills` stays, because it is what users type (`rf-agentskills:rf-browser`) and what every project setting and skill invocation names. The env vars `RF_AGENTSKILLS_*` used by hooks also stay: they are plugin behaviour, not the installer's identity. The installer module becomes `robotframework_plugins`, and its CLI becomes `robotframework-plugins`.

### D3 Versions and tags
Three kinds of version, each with one source:

| What | Scheme | Source of truth | Tag |
|---|---|---|---|
| Each plugin | SemVer | `plugins/<name>/.claude-plugin/plugin.json` | `<name>--v<version>`, e.g. `rf-agentskills--v3.1.0` |
| Installer `robotframework-plugins` | CalVer `YYYY.M.PATCH` | `installer/pyproject.toml` | `robotframework-plugins-v<version>` |
| `rf-skill-eval` | internal | root `pyproject.toml` | none |

- **Plugins:** the version lives only in `plugin.json`. Marketplace entries carry no `version`, and `marketplace.json` has no `metadata.version`; the generator and a test enforce both. Every `SKILL.md` `metadata.version` equals its plugin's version, so a skill copied on its own (tarball, Desktop ZIP) still says which release it came from. `scripts/bump-version.sh <plugin> <major|minor|patch>` writes all of them.
- **Plugin tags** follow Claude Code's `<plugin>--v<version>` convention, which plugin dependencies with version ranges resolve against. `release.yml` triggers on `*--v*` and releases that one plugin. The first release from the new home is `rf-agentskills--v3.1.0`: the content is unchanged apart from the manifests and the explicit subagent `tools` lists, and the rename breaks the install path, not the plugin. The old `v*` tags stay for existing pins; no new `v*` tag is made.
- **Installer:** calendar versions, because a release is a snapshot of the catalogue, not a version of any one plugin. The first release is numbered for the month it ships, for example `2026.12.0`; `PATCH` counts releases within a month. No zero padding, as PEP 440 normalises it away. A breaking CLI change is announced in the changelog one release ahead and called out in the release notes.
- **Version table:** the README, `docs/catalog.md`, `robotframework-plugins catalog` and every installer release note show which plugin versions the installer bundles. This table, not prose, answers "why is the installer 2026.12 and the plugin 3.1?".
- **Forwarding package:** the final `rf-agentskills` is `0.9.0`, depends on `robotframework-plugins>=<first CalVer release>`, and is built from a small package in `legacy/rf-agentskills/` that is deleted after it is published.
- *Rejected: lockstep, one number for the installer and every plugin.* A typo fix in one plugin would bump every other plugin and the installer, which doesn't work with several owners.
- *Rejected: independent SemVer for the installer, continuing at 0.9.0.* It works, but the gap to the plugin versions needs explaining forever. The new PyPI project has no version history to continue.
- *Rejected: an installer 3.x to match `rf-agentskills`.* It holds only while there is one plugin.
- *Rejected: resetting `rf-agentskills` to 1.0.0 under the new name.* `v1.1.0` and `v1.2.0` come with the history, so versions would collide.

### D4 A separate `catalog.yaml`, not extra keys in `plugin.json`
`plugin.json` is read by Claude Code, Copilot, Codex and Cursor, and `claude plugin validate` checks it. Unknown keys risk being rejected now or later. A separate `catalog.yaml` with its own JSON Schema can grow (for example review dates or eval links) without touching agent-facing manifests. The generator writes the marketplace `tags` from it, so the tier is still visible inside each agent's plugin browser.

### D5 The installer bundles the whole catalogue
The wheel's build hook copies every `plugins/<name>/` with status `active` or `deprecated` into `_assets/plugins/<name>/`, extending today's single-plugin mirror. `install` gets `--plugins`, with verified plugins as the default; there is a wizard step; and `catalog` lists what is bundled. The manifest records files per plugin, so uninstalling one plugin, or a plugin being removed, cleans up only that plugin. With one plugin today, the observable behaviour of `install` doesn't change.

### D6 Three security workflows with separate trust levels

```
security-gate.yml (on: pull_request)        security-deep-scan.yml               evals (existing)
  permissions: contents: read                 (on: pull_request_target, labeled    on: push to main,
  no secrets, forks included                   'security-deep-scan';                maintainer branches,
  1. house rules (own script)                  on: push to main)                    schedule
  2. Cisco skill-scanner (changed skills;      checks out PR head into ./pr as      never on fork code
     --lenient on changed agents and on        DATA; never runs it                  with secrets
     the whole shipped tree)
  3. SkillSpector --no-llm (changed            SkillSpector with model pass,
     skills/agents)                            Cisco model judge
  4. cc-audit -t mcp, -t plugin                secrets: model provider key only
  5. gitleaks on the diff                      permissions: pull-requests: write
  6. baseline compare -> fail on new HIGH+     posts a comment; sets a status check
  SARIF -> artifacts + job summary
  (code-scanning upload only on main)
```

- **Why tools are pinned:** each scanner is installed at an exact version, and checksum-verified where releases offer checksums, in its own virtualenv or as a release binary. The npm package named `cc-audit` links to no repository, so only the GitHub release binary is used.
- **Why Cisco also scans the whole tree:** only its lenient pass reads hooks and scripts. Without it, a hook that sends `process.env` to a remote host (canary C4) is a MEDIUM SkillSpector finding and passes. The cost is a CRITICAL `child_process` finding for every hook that starts a program, each reviewed once in the baseline.
- **Scanned files:** only what a plugin ships (its tracked files without `tests/` and `evals/`); the bundle's generated copy is judged by its member plugins' baselines (D15).
- **Why only changed plugins are scanned on PRs:** a full SkillSpector run of one plugin took 134 s. A nightly job scans everything, so baseline expiry and new scanner rules are noticed.
- **Why SARIF isn't uploaded to code scanning from PRs:** the upload needs `security-events: write`, which fork PRs don't get. Artifacts plus the job summary work for every PR.
- **The `pull_request_target` risk:** it runs with secrets. The job therefore never installs or executes anything from the PR, pins every action to a commit SHA, and passes the PR tree only as a path to scanners. A maintainer must apply the label, which is the review step of decision (a).

### D7 The house content rules are our own script
The rules in `content-security-scanning` are deterministic and specific to this repository: Unicode tags and zero-width characters, HTML comments in instruction files, explicit subagent `tools`, `allowed-tools` breadth, `curl | sh` in shipped code, unpinned MCP packages. They run in about a second and cover subagents and hooks, where external scanners are weakest. They live in `scripts/check_content_rules.py`, with tests that include the spike's canaries as fixtures.

### D8 Baselines record reviewed decisions
`security/baselines/<plugin>.yaml` holds entries `{scanner, rule, file, fingerprint, reason, reviewed_by, expires}`. A comparison script normalises each scanner's SARIF to `(scanner, rule, file, fingerprint)`. The first baselines are drafted from the spike's clean-run findings and reviewed entry by entry. Two spike findings get a decision instead of an automatic entry: `curl … | sh` for installing uv in `rf-setup` references, and lower-bound version pins in example `requirements.txt` files. Both are documentation examples, so the suggested decision is to accept them with a reason.

### D9 Approval from two groups needs a check, not just CODEOWNERS
On a protected branch, CODEOWNERS can require *one* approval from the owners of each changed path. It can't require approvals from two groups for the same file. A small `required-reviews` workflow reads the PR's changed paths and approvals through the API and fails until each required group has approved:
- the plugin's owners;
- the Foundation reviewers, for verified plugins;
- the security reviewers, for security-relevant paths.

It also checks that CODEOWNERS and `catalog.yaml` maintainers agree.

### D10 Writing in the Robot Framework Voice
The Foundation's voice guide is a draft and stays outside the repository. CONTRIBUTING.md summarises its rules in about ten lines: lead with what the reader gets, short modular sections, plain inclusive language, dry humour only outside install steps, errors and security text. A small lint enforces what can be checked mechanically: a banned-phrase list, and at most one exclamation mark per document. Everything else is a review checklist item. README drafts are reviewed against the guide before merge.

### D11 Adoption data without telemetry
- A scheduled weekly workflow stores the GitHub traffic API data (views, clones, referrers) as JSON on an `adoption-data` branch, since GitHub keeps it for only 14 days.
- PyPI downloads come from the public pypistats API.
- A quarterly workflow generates `docs/reports/adoption-<YYYY>-Q<n>.md` and opens a PR with it, so that a person reads the report before it is published.

### D12 Order of the switch-over
The new home has to work before the old one points to it, and the forwarding package has to exist before anyone is told to stop using `rf-agentskills`. See the Migration Plan.

### D13 Each plugin owns its sources, tests and evals
```
plugins/<name>/
  .claude-plugin/plugin.json   the plugin's one version
  catalog.yaml  CHANGELOG.md  README.md
  skills/  agents/  hooks/  scripts/  variants/
  tests/                       tests of this plugin's content
  evals/                       rf-skill-eval tasks and baselines for this plugin
eval/  tests/  scripts/        shared harness, repository checks and tooling only
```
- Root `skills/`, `scripts/sync-skills.sh` and the root-to-plugin half of `scripts/check-drift.sh` are removed; `plugins/<name>/skills/` is the source. `check-drift.sh` keeps checking the generated Codex and OpenCode variants. Release tarballs and Desktop ZIPs are built from `plugins/<name>/skills/` of the plugin being released.
- In other specs, a path `skills/<skill>/` means `plugins/<plugin>/skills/<skill>/`.
- PR CI runs the tests and evals of the plugins a PR changes, plus the shared tests; `main` and the nightly job run everything.
- `evals/` holds the plugin's tasks, trigger sets and baselines. The fixture projects (`eval/fixtures/`) and hidden grader suites (`eval/graders/`) stay shared, because tasks of several plugins use the same projects. `rf-skill-eval --plugin <name>` selects the plugin; without it the harness uses the only plugin with evals.
- `scripts/select-plugin-tests.py` maps a PR's changed paths to plugins: a change under `plugins/<name>/` selects that plugin, plus the plugins it depends on and those that depend on it (`plugin.json` `dependencies`); a change outside `plugins/` selects every plugin. CI runs the shared tests and each selected plugin's tests in separate pytest runs, so plugins may reuse test module names.
- Cost: Claude Code copies a marketplace plugin's whole folder, so `tests/` and `evals/` (about 1 MB for `rf-agentskills`) reach users' plugin caches. The installer's bundle and the release tarball leave them out.
- *Rejected: keeping root `skills/` with one subfolder per plugin.* It keeps a sync step and a second copy for no gain once each plugin has an owner.

### D14 Names are unique across the catalogue
Skill and subagent names must be unique across all active and deprecated plugins, and so must the paths a plugin's hooks and scripts are installed to. Inside Claude Code a plugin prefix separates them, but the installer's file mode and the release tarballs put every skill in one folder. The catalogue check enforces this.

### D15 Shared files are generated copies
*(Changed by `split-rf-agentskills` D5: Codex drops symlinks when it installs a plugin, so plugins carry none.)* When two plugins need the same file, for example a hook helper, one plugin owns it and the other carries a copy that the catalogue generator writes and `--check` keeps in step, as for the `rf-agentskills` bundle. Today only the bundle has copies; a generator entry for a file shared between two plugins is added when the first one exists. The earlier wording, kept for the record: one plugin owns it and the other links to it. Claude Code copies a symlink that points elsewhere in the marketplace as the target's content, and the installer's build hook does the same. The security gate scans the file once, at its owner, and a change to it counts as a change to every plugin that links to it.

### D16 A plugin is the unit of installation; a skill folder is the unit of ownership
Plugins group what users install together, by technology (`split-rf-agentskills`). Ownership goes by path in CODEOWNERS, so a library's maintainers can own their skill folder inside a shared plugin. A new plugin is warranted for a new technology with content and a maintainer group; otherwise a new skill joins an existing plugin. Moving a skill between plugins is a breaking release of both and is noted in both changelogs; the `renames` map can't follow it, because it maps plugin names, not skills.

### D17 Lifecycle uses the marketplace's own tools
The marketplace format has no deprecation state, so `deprecated` is a tag the generator adds to the entry, plus the README notice. Removing a plugin removes its entry and adds `"<name>": null` to the top-level `renames` map. Renaming a plugin adds `"<old>": "<new>"`. The map is append-only. `marketplace.json` sets `forceRemoveDeletedPlugins: true`, so Claude Code uninstalls a removed plugin, which matches what the installer does on upgrade.

## Risks / Trade-offs

- **Scanner noise blocks contributors** → the gate fails only on new HIGH+ findings not in a reviewed baseline; MEDIUM and lower are reported only; baseline changes go to the security team.
- **Scanners miss attacks.** Rules alone catch little, as both vendors say → the house rules, human review of security-relevant paths and the label-triggered model scans are layered; the docs say a clean scan proves nothing.
- **A scanner or its rule set is compromised** → exact versions, checksums where offered, no secrets in the gate, and version bumps to scanners reviewed like code.
- **`pull_request_target` leaks secrets** → no execution of PR content, SHA-pinned actions, a maintainer label required, and only the model-provider key exposed.
- **Users' install commands break** → the old repository is archived, not deleted, so old marketplace sources still resolve; the forwarding `rf-agentskills` package; the installer migrates old settings entries; the old README says how to switch.
- **History merge confuses tools that expect one root** → a single, documented merge commit; tags unchanged.
- **Foundation teams don't exist yet** → creating them is an early task, and branch protection is enabled after them. Until then the gate still runs, but the reviews it requires can't be enforced.
- **Bundling every plugin makes the wheel large** → acceptable while the catalogue is small. Revisit when the wheel passes 10 MB.

## Migration Plan

1. In the new repo: merge the history, push the tags, add the planning change, apply the renames and the catalogue and per-plugin layout (task groups 1–3). Then apply `split-rf-agentskills`, then the remaining programme files and CI (groups 4–9). Nothing is released yet.
2. Create the teams, branch protection, the `pypi` environment and the PyPI trusted publisher for `robotframework-plugins`.
3. Release the plugins from `split-rf-agentskills` (`rf-core`, `rf-web`, `rf-api`, `rf-mobile` and `rf-desktop` at 1.0.0, and the `rf-agentskills` 4.0.0 bundle) and the first CalVer installer release of `robotframework-plugins` from the new repo. `rf-agentskills--v3.1.0` is not released. Check installs on Claude Code, Copilot CLI and Codex from the new marketplace, and `uvx robotframework-plugins install`.
4. Publish the forwarding `rf-agentskills` 0.9.0 from the new repo, using the existing PyPI project's owner credentials or a trusted publisher added to that project.
5. In the old repo: a final README notice commit. Then archive the repository.

**Rollback:**
- Before step 3, delete the new branch and tags; nothing is published.
- After step 3, PyPI releases can be yanked but not deleted. The old repository stays usable until step 5, and archiving can be undone by an admin.

## Open Questions

- Who owns the PyPI projects: the user, or a Foundation PyPI organisation? Either way, trusted publishing is configured the same way.
- Who are the first members of the Foundation reviewers team and the security reviewers team, and what are the teams' exact GitHub names?
- Is a newer version of the Robot Framework Voice guide available? The draft provided is marked "old".
- Does the scheduled workflow's `GITHUB_TOKEN` have enough access for the traffic API, or does it need a fine-grained token with repository administration read access? Check in the first run of the collection workflow.
