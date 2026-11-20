## Why

`rf-language` teaches the mechanics of BDD in Robot Framework: steps are defined without a prefix, values go into embedded arguments, there is one `When` per scenario. It doesn't teach how to write a *specification*:
- how a feature, a rule and its examples map onto suites, documentation, metadata and tags;
- how to keep one step vocabulary across suites, and where scenario state lives;
- when an outline becomes a `Test Template` and when it becomes a separate test;
- how to translate pasted Gherkin or acceptance criteria into native `.robot`;
- how to review a suite for procedural steps, leaking state and drifting vocabulary.

A standalone `robotframework-bdd` skill was built and measured for this in the `bdd-agentskill` project, with 12 eval cases and two arms per case:
- **with the skill:** all 9 authoring cases passed every deterministic check, review recall was 1.00 and the rubric score 3.74 of 4;
- **without it:** 3 of 9 cases passed, recall was 0.89 and the rubric score 3.57.

The skill's largest effect was in greenfield cases, where nothing in the project sets the conventions. This change brings that skill into the catalogue under the repository's conventions, as `rf-bdd` in `rf-core`. Behaviour-driven test design applies to every system under test, and `plugin-split` puts test design in core.

## What Changes

- **New guidance skill `rf-bdd`** at `plugins/rf-core/skills/rf-bdd/`, ported from `bdd-agentskill/skills/robotframework-bdd`:
  - a compact description (≤ 160 characters, "Use" cue);
  - a `## When to use` block within the first 20 body lines, naming `rf-language` as its sibling;
  - a version gate;
  - Step 0, which matches the project's conventions;
  - house rules: three keyword layers; one behaviour per test; domain language; sentence-style step names (the default when the project has no convention); one vocabulary; the Gherkin-to-Robot Framework mapping; scenario state; independence; living documentation; imports;
  - **Write**, **Review** (no edits) and **Gherkin input** modes;
  - gotchas, a reference table and Companion Skills.
- **Seven references**, rewritten so that they don't duplicate `rf-language`:
  - `gherkin-mapping.md`, `step-design.md`, `state.md`, `data-driven.md`, `documentation-and-tags.md`, `robocop.md`, `review-checklist.md`;
  - generic embedded-argument matching, template mechanics and tag selection stay in `rf-language`; `rf-bdd` states the one-line rule and names `rf-language`.
- **Assets:**
  - `assets/robocop-bdd.toml`: NAME02/NAME18 set to `first_word_capitalized` with the possessive pattern, VAR06 ignored in `*_steps.resource`, and the format settings for template alignment and BDD-prefix separators;
  - runnable example projects in `assets/examples/`: a resource strategy (the default) and a World-library strategy, over a fake ATM service. They contain no library-specific keywords.
- **Project conventions win.** In a project that already writes Title Case steps, or imports resources by relative path, `rf-bdd` follows that convention. Sentence style plus the Robocop asset, and imports by name through `python-path`, are its defaults for greenfield projects only.
- **Native `.robot` only.** No `.feature` files, no Gherkin parser, nothing Robot Framework itself doesn't support. Pasted Gherkin is translated by meaning, and every wording change is listed for the author to confirm.
- **`rf-language` edits (content):**
  - its gotcha that BDD steps must be Title Case (robocop NAME18) becomes: follow the project's configured casing, and use `rf-bdd` for BDD specifications;
  - its BDD sections and the "When to use" block name `rf-bdd` as the sibling;
  - its Companion Skills table gets a `bdd` row.
- **Routing:**
  - the `UserPromptSubmit` context hook routes Given/When/Then and Gherkin work to `rf-bdd`, within its 450-character budget;
  - `rf-test-architect` routes BDD specifications to `rf-bdd`.
- **Evals in `rf-skill-eval` format** under `plugins/rf-core/evals/`:
  - a trigger set `triggers/rf-bdd.yaml` with ≥ 8 should-trigger and ≥ 8 should-not-trigger queries in both splits;
  - narrow, adversarial and realistic tasks ported from the `bdd-agentskill` cases;
  - a fixture `eval/fixtures/sut-bdd-library` and hidden graders `eval/graders/bdd/`;
  - baselines measured on the current CI model.
- **Tests:** `plugins/rf-core/tests/test_bdd_skill.py` checks structure, the reference table, dry runs and real runs of every example, and that the Robocop asset lints the examples cleanly on the pinned Robocop.
- **Changelog and docs:**
  - no version bump: every plugin shares the release version, and the PR adds a line under `## Unreleased` in `CHANGELOG.md`, in the `rf-core` group (new content, so the next release is a minor one);
  - the `rf-core` README, the repository README's plugin table and the catalogue summary.

No breaking change: no skill is removed or renamed.

## Capabilities

### New Capabilities
- `bdd-skill`: the `rf-bdd` agent skill for writing and reviewing behaviour-driven Robot Framework specifications in native `.robot` files. It defines frontmatter and layout, the description and sibling boundary, the SKILL.md skeleton and size budget, the reference set, the version gate, Step 0 convention matching and greenfield defaults, the house rules, the Write/Review/Gherkin-input modes, the Robocop asset, runnable examples, gotchas, the no-parser rule, and the trigger set, eval tasks and tests.

### Modified Capabilities
- `language-skill`: the scope-boundary and Companion Skills requirements name `rf-bdd`. BDD specification design (feature/rule mapping, vocabulary, state, review) is out of scope and belongs to `rf-bdd`.
- `skill-triggering`: `rf-language` ↔ `rf-bdd` becomes a sibling pair, with its signal, in "Sibling skills state their boundary", and both are listed in "Sibling skills share a plugin".
- `plugin-split`: the `rf-core` row of the plugin table lists `rf-bdd`, and the skill count becomes ten.
- `rf-session-context-hooks`: the injection routes Given/When/Then and Gherkin work to `rf-bdd`, and the trigger matches the `rf-bdd` identifier.
- `plugin-subagents`: the routing table sends BDD specifications (Given/When/Then suites, step vocabularies, Gherkin translation) to `rf-bdd`.

## Impact

- **New**:
  - `plugins/rf-core/skills/rf-bdd/`: `SKILL.md`, 7 references, `assets/robocop-bdd.toml`, `assets/examples/`;
  - `plugins/rf-core/tests/test_bdd_skill.py`;
  - `plugins/rf-core/evals/triggers/rf-bdd.yaml`, task YAMLs under `plugins/rf-core/evals/tasks/{narrow,adversarial,realistic}/`, baselines;
  - `eval/fixtures/sut-bdd-library/` and `eval/graders/bdd/`, plus a custom grader module if the existing check types don't cover the BDD structure checks.
- **Edited**:
  - `plugins/rf-core/skills/rf-language/`: `SKILL.md` (When to use, Gotchas, Companion Skills) and `references/styles.md`, `references/embedded-arguments.md` (one-line pointers);
  - `plugins/rf-core/scripts/maybe_inject_rf_context.mjs` and its tests;
  - `plugins/rf-core/agents/rf-test-architect.md`, then `scripts/build-agent-variants.py` for the generated variants;
  - `tests/test_skill_descriptions.py` (catalogue key `bdd`, required rows), with listing room checked: about 890 of 1210 characters are used today;
  - `CHANGELOG.md` (`## Unreleased`, rf-core group), `plugins/rf-core/README.md`;
  - `.claude-plugin/marketplace.json` and the README catalogue, if `build-catalog.py` changes them;
  - `security/baselines/rf-core.yaml`, only if the scanners flag the new example Python files.
- **Review**: `rf-core` is `verified`, so the PR needs a Foundation reviewer. The `tools`/`allowed-tools` fields are unchanged, but the hook script changes, so it also needs a security reviewer.
- **Dependencies**: none new at run time. DataDriver appears only in a reference; installing it is `rf-setup`'s job. The examples need Robot Framework ≥ 7.3 (typed embedded arguments) and are verified against the pinned 7.4.2 and against 7.5.1.
