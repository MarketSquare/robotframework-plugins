# Contributing

You can add a plugin for a library or tool that isn't covered yet, or improve one that is: fix a skill, add a reference, sharpen a subagent. This page covers how to do either, the checks your PR must pass, how review works, how to write the text, and which version to bump.

## Add a plugin

1. Copy `templates/plugin/` to `plugins/<name>/`. Plugin names start with `rf-` and describe the technology, for example `rf-database`.
2. Fill in `catalog.yaml`: a one-line summary, `tier: community`, `status: active`, yourself under `maintainers`, the libraries with the version ranges you checked, the Robot Framework range and the agents you tried. The schema is `schemas/catalog.schema.json`.
3. Rename the example skill to `rf-<topic>` (the folder name and the `name` in `SKILL.md` must match) and write it. Skill and subagent names must be unique across every plugin.
4. Add a line for your plugin to `.github/CODEOWNERS` with the same people as `maintainers`.
5. Regenerate the catalogue and the marketplace: `python scripts/build-catalog.py`.

A new plugin starts in the `community` tier. [GOVERNANCE.md](GOVERNANCE.md) says what `verified` needs.

## Change a plugin

Edit the files under `plugins/<name>/`; that folder is the only copy of its content. Then regenerate what is generated from it:

```bash
python scripts/build-agent-variants.py   # after changing a subagent or hooks/hooks.json
python scripts/build-catalog.py          # after changing a catalog.yaml, a version, or any plugin the bundle copies
```

A file that more than one plugin needs lives in one of them; the others get a generated copy. Plugins can't contain symlinks, because Codex drops them on install.

## Checks a PR must pass

CI runs these on every PR. Run them locally first:

| Check | Command |
|---|---|
| Catalogue, names, symlinks, lifecycle | `python scripts/build-catalog.py --check` |
| Ownership and tier evidence | `python scripts/check-governance.py` |
| House content rules | `python scripts/check_content_rules.py` |
| Skill frontmatter | `python scripts/validate-skills.py --channel all` |
| Cross-plugin references | `python scripts/check-plugin-references.py` |
| Generated variants | `bash scripts/check-drift.sh` |
| Docs voice | `python scripts/check-docs-voice.py` |
| Tests | `python -m pytest tests/ --ignore=tests/eval` and `python -m pytest plugins/<name>/tests` |

The security gate also scans the plugins your PR changes with Cisco skill-scanner, SkillSpector, cc-audit and Gitleaks. To run it locally: `scripts/install-scanners.sh`, then `scripts/security-scan.sh <plugin> out/`. It fails on a new HIGH or CRITICAL finding. If a finding is a false positive, add an entry with a reason to `security/baselines/<plugin>.yaml`; the security reviewers approve every baseline change.

Live agent evals (`rf-skill-eval`) run on maintainer branches, after merge and weekly, never on code from forks. A maintainer runs them for your PR when it changes skill content.

## Review

The PR template has a checklist: purpose, supported versions, examples, security-relevant changes, tool permissions and documentation voice. Tick each item or write "n/a" with a reason.

The `required-reviews` check waits for an approval from each group your PR concerns:

- a maintainer of every plugin it changes;
- a Foundation reviewer, when one of those plugins is `verified` or the PR promotes one;
- a security reviewer, when it changes hooks, scripts, MCP configuration, manifests, subagent `tools`, skill `allowed-tools`, the workflows or `security/`.

Your own approval doesn't count.

## Writing

Text for people (READMEs, these documents, skill references) follows the Robot Framework Voice:

- Open with what the reader gets or can do. No mission statements.
- Use short sections with headings that say what's in them, and lists for steps and options.
- Use plain, inclusive words. Explain jargon the first time.
- Say what to do, not how great it is: "Install `rf-core`", not "Get started with our amazing tooling".
- Keep humour dry and rare, and never in install steps, error messages or security text.

`scripts/check-docs-voice.py` catches the mechanical part: a list of banned phrases and more than one exclamation mark per document. Reviewers check the rest.

`SKILL.md` files are written for agents: lead with when to use the skill, keep the description under 160 characters, and put depth in `references/`.

## Versions

There are three kinds of version, and as a plugin author you only ever bump one of them.

| What | Example | Where it lives | Who bumps it |
|---|---|---|---|
| A plugin | `rf-core` 1.0.0, the `rf-agentskills` bundle 4.0.0 | its `plugin.json` | the plugin's maintainers |
| The installer | `robotframework-plugins` 2026.11.0 | `installer/pyproject.toml` | the release manager |
| The eval harness | `rf-skill-eval` 0.1.0 | root `pyproject.toml` | nobody outside CI; it is never published |

A plugin has SemVer: bump `major` for a removed or renamed skill, `minor` for new content, `patch` for fixes. Each plugin counts on its own, which is why `rf-core` can be at 1.0.0 while the bundle is at 4.0.0: the bundle carries on the numbering of the single plugin it replaced.

The installer uses calendar versions, because each release is a snapshot of the whole catalogue taken in that month. The version table in the README shows which plugin versions an installer release bundles:

| robotframework-plugins 2026.11.0 bundles | Version |
|---|---|
| `rf-core` | 1.0.0 |
| `rf-web` | 1.0.0 |

To bump your plugin, run one command and regenerate:

```bash
scripts/bump-version.sh <plugin> <major|minor|patch>
python scripts/build-catalog.py
```

It writes `plugin.json` and the `metadata.version` of every skill in the plugin. Releases are described in [RELEASING.md](RELEASING.md).

## Development

### Layout

```
.claude-plugin/marketplace.json  # The marketplace every plugin-capable agent reads (generated)
plugins/<name>/                  # One folder per plugin; the only copy of its content
├── .claude-plugin/plugin.json   # The plugin's one version
├── catalog.yaml                 # Programme manifest: tier, status, maintainers, libraries
├── skills/rf-*/                 # One folder per skill; folder name == SKILL.md name
│   ├── SKILL.md                 # Skill definition (loaded by agent)
│   ├── scripts/                 # Python scripts (executed, not loaded)
│   └── references/              # Deep reference docs (loaded on demand)
├── scripts/                     # Hook scripts (.mjs)
├── agents/                      # Subagent definitions
├── hooks/                       # Session and edit hooks
├── variants/                    # Generated: Codex TOML subagents, OpenCode agents and JS plugin
├── tests/                       # The plugin's own tests (not installed)
└── evals/                       # Eval tasks, trigger sets and baselines (not installed)
bundles/rf-agentskills/          # Generated copy of the bundled plugins
schemas/catalog.schema.json      # Schema of catalog.yaml
security/                        # Scanner baselines and configuration
templates/plugin/                # Starter plugin
installer/                       # The robotframework-plugins Python installer
tests/                           # Shared tests: repository, catalogue, installer, eval harness
eval/                            # Shared eval harness content: fixture projects and hidden graders
scripts/                         # Build and check utilities
```

`scripts/export-skills.py` writes standalone copies for the release tarballs and Claude Desktop archives, with plain `scripts/x.py` commands instead of the plugin's `"${CLAUDE_SKILL_DIR}/scripts/x.py"`.

### Tests

The shared tests and each plugin's tests run separately, because plugins may reuse test file names:

```bash
python -m pytest tests/ --ignore=tests/eval -v      # shared: repository, catalogue, installer
python -m pytest plugins/rf-core/tests/ -v          # one plugin
python -m pytest plugins/rf-core/tests/test_hook_scripts.py -v   # needs robotcode[all] for the validation tiers
```

In a PR, CI runs the shared tests plus the tests of each plugin the change touches, and of the plugins that depend on it; a change outside `plugins/` runs every plugin's tests (`scripts/select-plugin-tests.py`).

### Skill evaluations

The eval harness (`rf-skill-eval`) grades each skill in controlled Claude Code sessions. See [docs/ci/usage.md](docs/ci/usage.md). Quick start:

```bash
cp .env.example .env      # add your CLAUDE_CODE_OAUTH_TOKEN
uv sync
uv run rfbrowser init
uv run rf-skill-eval doctor
bash scripts/eval-local.sh
```

It reads a plugin's eval content from `plugins/<name>/evals/`; pass `--plugin <name>`, or `--plugin all` for every plugin.

### Bundled scripts

Skills run their Python scripts directly (`uv run python scripts/<name>.py …`, or the project's interpreter). Each prints JSON:

| Script (skill) | Purpose |
|---|---|
| `rf_conventions.py` (rf-language) | Report a project's Robot Framework conventions and version |
| `check_library.py` (rf-python-library) | Check the project's own Python keyword libraries: keywords, scope, API style and defect findings (runs in a subprocess, never imports user code into the agent) |

### Try a plugin locally

```bash
claude --plugin-dir ./plugins/rf-core --plugin-dir ./plugins/rf-web
```

Claude Desktop loads skills uploaded as ZIP files: build them with `python scripts/build-skill-zips.py --out dist/skill-zips`.
