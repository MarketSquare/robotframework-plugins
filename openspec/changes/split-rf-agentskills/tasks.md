Prerequisite: `launch-plugin-programme` task groups 1–3 are done (history merged, renames applied, catalogue and per-plugin layout in place).

## 1. Spike: dependencies and symlinks

- [ ] 1.1 Build a scratch marketplace with a plugin `dep-a` (one skill, one hook), a plugin `dep-b` that depends on `dep-a`, and a bundle that depends on both and also symlinks one skill from `dep-a`. Install the bundle in isolated homes on Claude Code, Copilot CLI and Codex at their current versions. Record, per agent, whether the dependencies install, whether the skills and the hook load, and whether the symlinked skill loads. Verify by attaching the per-agent results table to this change's design (D5).
- [x] 1.2 *(Skipped with the maintainer's agreement: Codex drops symlinks on every platform, so none ship and the Windows checkout can't change the decision; see design D5.)* Clone the scratch marketplace on Windows with `core.symlinks=false` (GitHub Actions `windows-latest`) and install it in Claude Code there. Verify by recording whether the symlinked skill arrives as content, as a text file holding a path, or not at all.
- [x] 1.3 Choose the D5 row that matches the results and record the decision in design.md. Verify that the bundle mechanism and the shared-file mechanism are each named once, with the spike evidence.

## 2. Create the plugins

- [x] 2.1 Create `plugins/rf-core`, `rf-web`, `rf-api`, `rf-mobile` and `rf-desktop`, moving skills, subagents, hooks, scripts, variants, tests and evals with `git mv` from `plugins/rf-agentskills/` as the `plugin-split` table assigns them. Verify that `git log --follow plugins/rf-web/skills/rf-browser/SKILL.md` reaches the original commits, and the "Every skill has one home" scenario.
- [x] 2.2 Write each plugin's `plugin.json` (version 1.0.0; technology plugins depend on `rf-core` `^1.0`), `catalog.yaml` (libraries with PyPI `package` names), README and CHANGELOG, and add CODEOWNERS paths per skill folder. Verify that `claude plugin validate .` passes and the "Installing web brings core" scenario passes in an isolated Claude Code home.
- [ ] 2.3 Turn `plugins/rf-agentskills/` into the 4.0.0 bundle using the mechanism chosen in 1.3, with a changelog entry on the prefix change. Verify the "Existing project settings keep working" and "Bundle on Copilot CLI and Codex" scenarios in isolated homes.
- [x] 2.4 Add the catalogue check that refuses a plugin without content. Verify the "Empty plugin refused" fixture.

## 3. Move library-specific content out of core

- [ ] 3.1 Move each library's post-install steps from `rf-setup` into `references/install.md` of its library skill, and update each library skill's install block. Reduce `rf-setup`'s library section to the one-row-per-library table naming skill and plugin. Update `test_library_install_guidance.py` and `test_setup_skill.py`. Verify the modified `library-skill-install-guidance` and `setup-skill` scenarios.
- [ ] 3.2 Move the SeleniumLibrary→Browser table into `rf-browser/references/migrate-from-selenium.md` and the RequestsLibrary→RESTinstance table into `rf-restinstance/references/migrate-from-requests.md`, and change `rf-migration-guide` to route library moves to them. Verify the "Migration tables live in library skills" scenario and that the subagent body stays within 120 lines.
- [ ] 3.3 Verify the "Library-specific content outside core" scenario with a test that searches `plugins/rf-core/`.

## 4. Cross-plugin references

- [ ] 4.1 Qualify every reference to a technology skill in `rf-core` (skills, subagents, hook text) with its plugin, and add the "suggest installing the plugin" line to the three subagents. Regenerate the Codex and OpenCode variants. Verify the "Every routed skill exists" and "Missing library skill" scenarios, and the variant drift check.
- [ ] 4.2 Write the cross-plugin reference lint and add it to CI. Verify the "Lint finds an unqualified reference" fixture.
- [ ] 4.3 Rewrite the context-injection text to route library work generically and name only `rf-core` skills and the technology plugins, within 450 characters. Verify the modified `rf-session-context-hooks` scenarios and the budget test.
- [ ] 4.4 Make the `SessionStart` report name the plugin and its per-agent install command for each detected library. Verify the "Browser found" and "Nothing to suggest" scenarios, and that the hook still exits 0 on malformed input.

## 5. Installer

- [x] 5.1 Add project detection: read `pyproject.toml` (PEP 621, Poetry, dependency groups) and `requirements*.txt`, and match against `catalog.yaml` packages. Apply the fresh-install and upgrade defaults, `--plugins all`, wizard preselection, and the printed reason. Verify the "Browser project" and "Nothing detected" scenarios.
- [ ] 5.2 Change the file-mode layout to `<root>/<plugin>-files/`, record files per plugin, and on upgrade move `rf-agentskills-files/`, rewrite hook commands and keep user-modified files. Verify the "Claude Code file-mode upgrade" and "Narrowing is explicit" scenarios for Claude Code, Codex, Cursor and OpenCode.
- [ ] 5.3 Check plugin mode with the split: `enabledPlugins` gets one entry per selected plugin, and migrated old settings enable the bundle. Verify the launch change's "Old marketplace entry migrated" scenario still passes, plus a new test with `--plugins rf-core,rf-web`.

## 6. Evals

- [ ] 6.1 Add trigger staging for partial installs (`rf-core` plus one technology plugin) and the cross-technology measure. Verify the "Web only" scenario on Haiku 5.5 and Sonnet 5.5.
- [ ] 6.2 Add one partial-install task per technology plugin and the coverage check. Verify the "Browser task with core only" and "Every technology plugin covered" scenarios.
- [ ] 6.3 Re-run the trigger and narrow evals for all nine skills with all plugins staged, on Haiku 5.5 and Sonnet 5.5, with at least 3 replicates. Verify that no skill falls below its 3.0.0 baseline beyond the gate's tolerance; in particular, check `rf-setup` and the library skills after the install move.

## 7. Launch plan and docs

- [ ] 7.1 Re-check D10 against `launch-plugin-programme` as it stands when this change is applied (the non-goal, D16, task order, 10.2 and the `package` field were edited when this change was proposed), and update any of its spec deltas that name `rf-agentskills` as the only plugin where that is now false. Verify that `openspec validate --strict` passes for both changes.
- [ ] 7.2 Update the README catalogue and install sections, `docs/catalog.md` and the version table for six plugins, with the prefix-change note. Verify the docs voice check and the catalogue `--check`.
- [ ] 7.3 Verify end to end in isolated homes, before release: fresh install of `rf-core` + `rf-web` on Claude Code, Copilot CLI and Codex from the marketplace; `uvx robotframework-plugins install --agent claude-code --yes` in a Browser project; and an upgrade from `rf-agentskills` 0.8.0.
