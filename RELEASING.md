# Releasing

One release publishes everything at once: every plugin through the marketplace, and the `robotframework-plugins` installer on PyPI. All of them carry the same version, and one tag, `v<version>`, releases them.

## The version

| What | Version | Source of truth |
|---|---|---|
| Every plugin (`rf-core`, `rf-web`, …) and the installer | SemVer, for example `5.0.0` | `installer/pyproject.toml` |
| `rf-skill-eval` (internal) | SemVer | root `pyproject.toml`; never published |

`scripts/build-catalog.py` copies the version into every `plugin.json`, the installer's `__version__`, the README and `docs/catalog.md`. Its `--check` fails when a copy differs, so nobody edits those by hand. The marketplace entries carry no version: agents read it from `plugin.json`.

Which part to bump depends on the whole release, every plugin and the installer together:

- **major**: a plugin is removed; a skill, subagent or hook changes in a way users must act on (a renamed or removed skill, a new requirement); the CLI or the Python API breaks.
- **minor**: a new skill, plugin or feature.
- **patch**: fixes and wording.

A major change in one plugin also gives every other plugin the new major number. The changelog says which plugin changed, and "no changes" for the others.

Versions stay above `3.0.0`: the tags `v1.1.0` to `v3.0.0` are the old `rf-agentskills` content releases, and the catalogue check and the release workflow refuse anything at or below them.

## Make a release

1. On a branch, bump the version:
   ```bash
   scripts/bump-version.sh <major|minor|patch>
   ```
   It sets `installer/pyproject.toml` and `uv.lock`, regenerates every copy, and turns `## Unreleased` in `CHANGELOG.md` into `## <version> — <date>`.
2. Read that changelog section: breaking changes first, then one group per plugin and one for the installer. The release notes are built from it.
3. Check the skills on Claude. CI evaluates PRs on an OpenRouter model, so run a manual Claude evaluation of the branch and check its gate against the Claude baselines:
   ```bash
   gh workflow run skill-evaluation.yml --ref <branch> \
     -f provider=claude -f model=claude-sonnet-5-5 -f tiers=narrow,realistic -f arms=treatment,baseline
   ```
4. Open the release PR and merge it once every check is green.
5. Tag the merge commit and push the tag, on its own:
   ```bash
   git tag v<version> <merge commit> && git push origin v<version>
   ```
6. `release.yml`:
   - checks the tag against the version and every `plugin.json`, and refuses anything not above `3.0.0`;
   - runs CI;
   - builds every plugin's archives, the per-skill upload archives, the wheel and the sdist;
   - creates one GitHub release from the changelog section.
7. Approve the `pypi` environment's deployment in the workflow run. The publish job uploads with **trusted publishing**: PyPI accepts the upload from this repository's workflow without a token, and nobody handles a PyPI token. After the upload, the workflow moves `stable` and `latest` to the tag.
8. Check the published package:
   ```bash
   uvx --refresh robotframework-plugins@<version> version
   ```

A pushed tag is the ref users pin a marketplace to: never move or delete one.

## Release candidates

`scripts/bump-version.sh --rc <major|minor|patch>` starts a candidate, for example `5.1.0rc1`. Run it again to get `rc2`, and without `--rc` to finish the release (`5.1.0`). Plugins carry the SemVer form, `5.1.0-rc.1`. The tag is `v5.1.0rc1`. A candidate publishes to TestPyPI and is marked as a pre-release on GitHub, and `stable` and `latest` stay where they are.

## Release notes

`python scripts/build-catalog.py --release-notes <version>` writes them:
- how to pin the release and install the installer;
- the changelog section;
- the plugins in the release, with their tiers;
- the attached archives.

The changelog section names every plugin that was added, deprecated, demoted or removed ([GOVERNANCE.md](GOVERNANCE.md)).
