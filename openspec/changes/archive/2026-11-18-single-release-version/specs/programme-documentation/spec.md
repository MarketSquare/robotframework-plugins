## MODIFIED Requirements

### Requirement: Required documents

The repository SHALL contain:
- `README.md`: what the marketplace is, the generated catalogue, install per agent, the trust tiers in short, and links to the other documents;
- `CONTRIBUTING.md`: how to add or change a plugin, the checks a PR must pass, the writing rules, and a short section on versions. That section says that every plugin and the installer share the release version, that contributors never bump it, and that `rf-skill-eval` keeps its own internal version;
- `CHANGELOG.md`: the one changelog of every release, as `release-train` defines;
- `GOVERNANCE.md`: tiers, review, maintainer expectations and lifecycle;
- `SECURITY.md`: see `content-security-scanning`;
- `RELEASING.md`: the one release (Semantic Version, `v<version>` tag, which part to bump), release candidates, and the PyPI publishing flow;
- `templates/plugin/`: a starter plugin with `catalog.yaml`, a README and one example skill that passes every check;
- the installer README published on PyPI.

#### Scenario: Template plugin passes CI
- **WHEN** CI copies `templates/plugin/` to `plugins/example/` in a scratch checkout and runs every PR check
- **THEN** all checks pass

### Requirement: Contributors can tell which version to bump

`CONTRIBUTING.md` SHALL explain, in at most one screen, that every plugin and the installer carry the same release version, that a contributor adds a changelog entry under "Unreleased" instead of bumping anything, and that a maintainer sets the version with `scripts/bump-version.sh <major|minor|patch>` when releasing.

#### Scenario: Version question answered
- **WHEN** a contributor asks which version to bump after changing `rf-web`
- **THEN** the "Versions" section of `CONTRIBUTING.md` says none, and names the `CHANGELOG.md` "Unreleased" section as the place for the entry
