## Context

The source is `bdd-agentskill/skills/robotframework-bdd` (archived change `2026-11-12-add-robotframework-bdd-skill` in that project): `SKILL.md` (151 lines), seven references (1,188 lines), a Robocop asset and two example projects. It was measured with a custom harness (`claude -p`, an LLM judge, Sonnet) against Robot Framework 7.5.1, robotcode 2.9.0.dev186 and Robocop 9.4.0. See proposal.md (Why) for the results.

Constraints in this repository that shape the port:
- **Pinned tools.** The lockfile pins Robot Framework 7.4.2, robotcode 2.8.0 and Robocop 8.2.10. The `rf-language` tests use Robocop 9.x through `uvx` when it isn't installed.
- **Compact descriptions.** At most 160 characters, a "Use"/"Load" cue, and a listing total of at most 1,210 characters; about 890 are used today. The `## When to use` block must come within the first 20 body lines.
- **Overlapping guidance.** `rf-language` already has BDD basics in `references/styles.md` and `references/embedded-arguments.md`. Its gotcha requires Title Case BDD steps (NAME18 default), and it imports by relative path or `${CURDIR}`.
- **Hook budget.** The context hook message is 449 of its 450-character budget.
- **Tier.** `rf-core` is `verified`: a new skill needs a trigger set, eval tasks and baselines (GOVERNANCE.md), and the PR needs a Foundation reviewer.
- **Evals.** Their format is `rf-skill-eval` YAML with typed checks, gating flags and `custom_python` graders in `src/rf_skill_eval/scoring/custom/`. Fixtures live in `eval/fixtures/` and hidden graders in `eval/graders/`.
- **Shipped content.** It must pass `check_content_rules.py`, `check-docs-voice.py`, `check-plugin-references.py` and the security scanners. Plugins contain no symlinks.

## Goals / Non-Goals

**Goals:**
- `rf-bdd` that works next to `rf-language` and doesn't contradict it: the agent loads both and gets one answer per question.
- The measured behaviour of the source skill survives the port: deterministic checks pass in greenfield cases, the review finds the seeded issues, and the no-parser rule holds.
- Every example and code block runs on the pinned Robot Framework 7.4.2, and also on 7.5.1.

**Non-Goals:**
- Porting the `bdd-agentskill` harness (`run_evals.py`, LLM judge, rubric). Only its cases are ported, as `rf-skill-eval` tasks.
- A Gherkin parser, `.feature` support, or a BDD-specific hook.
- A Python script for the skill. Step 0 uses `rf-language`'s conventions report and grep fallbacks, so no second detector is shipped.
- Changing `rf-language`'s examples or its default Title Case style for non-BDD keywords.

## Decisions

**D1. A skill in `rf-core`, not a new plugin.**
`plugin-split` gives test design to core, and "Sibling skills share a plugin" asks siblings to ship together. A user with `rf-language` therefore always gets the boundary text and the BDD skill.
- *Alternative:* a community plugin `rf-bdd`. It would be easier to enter, but the sibling pair would be split across two plugins, users would need a second install for a technology-independent skill, and the catalogue would gain a plugin with one skill and no library.

**D2. The skill name is `rf-bdd`.**
It follows the `rf-<topic>` rule and is short in the listing.
- *Alternatives:* `rf-bdd-specs` or `rf-specification`. They are longer, and "BDD" is what users type.

**D3. Project conventions win; sentence style is the greenfield default.**
Step 0 reads the casing of existing step keywords and the import style.
- If steps exist, rf-bdd follows them and leaves the Robocop configuration alone.
- If there are none, it writes sentence-style steps and merges `assets/robocop-bdd.toml` into the project configuration. The hook runs Robocop with the project's configured rule set, so the merged settings also silence the hook's NAME18 warnings.

`rf-language`'s casing gotcha is reworded to "follow the project's configuration", which makes the two skills agree. Imports follow the same rule: by name through `python-path` by default, relative where the project already imports that way. (User decision, 2026-11-18.)
- *Alternative:* Title Case everywhere. The source evals preferred sentence style for readability, and its Robocop settings were verified to work.
- *Alternative:* sentence style repo-wide. That would rewrite `rf-language`'s examples and evals, which is out of scope.

**D4. Port, don't copy: rf-bdd owns the specification, rf-language keeps the mechanics.**
Each source reference section is sorted into one of two kinds:
- *BDD design*, which stays: feature/rule mapping, vocabulary, state strategies, the outline-fits-every-row rule, living docs, the review checklist, Gherkin translation.
- *Robot Framework mechanics*, which becomes one line naming `rf-language`: embedded-argument matching and conflicts, template status rules, tag patterns, `__init__.robot` visibility.

The source's robotcode command table is cut to the BDD-specific uses (`doc keywords` on step resources, `discover tests` for tags), and the rest is left to the robotcode skill.

References follow `rf-language`'s house rules: no links between references, a table of contents above 100 lines, and every reference in the reference table. The SKILL.md skeleton is rf-bdd's own (spec `bdd-skill`), because `rf-language`'s skeleton sections (keyword anatomy, tags and selection) don't apply.

**D5. Version gate: floor RF 7.0, examples RF 7.3+.**
The examples use typed embedded arguments (`${amount: int}`), which need 7.3. That covers the pinned 7.4.2 and the CI model's fixtures.
- The gate gives `${n:\d+}` with explicit conversion as the form for older versions.
- Test-level `[Metadata]` (7.5) appears only as a gated note. The examples use suite `Metadata`, so they run on 7.4.2.

Every code block is verified on 7.4.2 (the lock) and 7.5.1.

**D6. The Robocop asset must work on Robocop 8.2.10 and 9.x.**
The source was verified on 9.4.0 only. Implementation runs the asset under both versions.
- Where a setting differs (for example `per-file-ignores`, or the formatter's `skip_keyword_call_pattern`), `references/robocop.md` states the version.
- If a setting has no 8.x form, it states the fallback: an inline `# robocop: off=VAR06` in the steps resource.

The structure test lints the examples with the installed Robocop, falling back to `uvx` like the `rf-language` tests do.

**D7. Examples are self-contained and library-neutral.**
- They keep the fake ATM SUT (`AtmService.py`) and the two strategy projects, under `assets/examples/{sut,resource-strategy,world-strategy}/`.
- They contain no Browser or Requests keywords, as `plugin-split` requires for core.
- Each `robot.toml` uses relative `python-path` entries inside the example tree. There are no symlinks.
- The scratch tool `check_examples.py` from the source project becomes the code-block layer of `test_bdd_skill.py`, which extracts `<!-- file: … -->` blocks, dry-runs them and runs them for real.

**D8. Fit the hook message by tightening existing wording.**
The router line gains `Given/When/Then specs -> rf-bdd;`. To make room, existing phrases are shortened without dropping a route, for example "Robot Framework context detected. Load the matching skill before writing RF:" becomes "RF context: load the matching skill first:". The 450-character test stays unchanged.
- *Alternative:* raising the budget. Rejected, because the budget is a spec requirement chosen for token cost.

**D9. Co-loading is expected; rf-language's trigger set stays as it is.**
The BDD queries in `rf-language.yaml` (`lang-t02`, `lang-t14`) stay should-trigger, because rf-bdd tells the agent to load rf-language for syntax. Validation queries are never edited.

`rf-bdd.yaml` gets:
- BDD positives: specification wording, pasted Gherkin, review for readability;
- negatives: plain RF syntax, Python library, results, Cucumber/Java, pytest-bdd, SpecFlow.

The re-baseline of all rf-core descriptions runs before rf-bdd is staged, so any recall change in rf-language from the new neighbour is visible. A drop below the stored baseline blocks the change, per skill-triggering.

**D10. Evals: port five source cases, grade with a custom module.**

| Source case | Task | Tier |
|---|---|---|
| `author-greenfield` | `narrow-bdd-greenfield-01` | narrow |
| `author-outline` | `narrow-bdd-outline-01` | narrow |
| `author-extend-vocabulary` | `narrow-bdd-extend-vocabulary-01` | narrow |
| `author-gherkin-request` | `adv-bdd-gherkin-row-01` ("1 days" row) | adversarial |
| `review-procedural` | `narrow-bdd-review-01` | narrow |

The fixture is `eval/fixtures/sut-bdd-library`: the source `library-base` (a lending service with fixed dates), plus `library-steps` for the vocabulary task and `review-procedural` for the review task, as overlays selected by task.

Gating uses existing checks where they fit: `robot_pass` with `expected_tests`, `file_not_contains` for `.feature` and `GherkinParser`, and `file_exists`. A new `src/rf_skill_eval/scoring/custom/bdd.py` ports the source graders:
- `structure`: AST check that test bodies hold only BDD-prefixed calls or template rows;
- `living_docs`: suite documentation and `Metadata Feature` or feature tags;
- `review_findings`: no file changed, and the final message names at least N of the seeded check IDs or their issue keywords.

No LLM judge gates a task. The remaining source cases (DataDriver, German, World library, table/docstring, background, the two other review cases) are listed as follow-up candidates, not ported now. That keeps CI cost in line with the other rf-core skills, which have 5 to 7 tasks each.

**D11. Versions.**
Since 5.0.0 every plugin and the installer share one version, set only at release time (`release-train`).
- The PR bumps no version, and `rf-bdd` carries no `metadata.version` (the validator refuses it).
- It adds a line under `## Unreleased` in `CHANGELOG.md`, in the rf-core group. New content makes the next release a minor one; the release manager runs `scripts/bump-version.sh minor`.
- `build-catalog.py` regenerates the marketplace and the catalogues. There is no bundle any more.

## Risks / Trade-offs

- **[Risk]** Adding a tenth description reduces the room for the others, and a future Claude Code release shrinks the room further. → **Mitigation:** keep rf-bdd's description to about 100 characters, so the total stays under 1,000 of the 1,210 allowed. The trigger gate reports a skill that is listed by name only.
- **[Risk]** rf-language starts losing BDD-flavoured queries to rf-bdd, or rf-bdd fires on plain "write a robot test". → **Mitigation:** run the re-baseline first, include negatives aimed at rf-language in rf-bdd's set, and apply the acceptance rule that neither skill's validation result may drop below its baseline.
- **[Risk]** Robocop 8.2.10 lacks a setting the asset uses. → **Mitigation (D6):** state the version in the reference and document the inline fallback. Test on both versions.
- **[Risk]** The source results were measured on Sonnet with an LLM judge, while CI here uses GLM 5.3 Flash on OpenRouter with deterministic checks, so the numbers aren't comparable. → **Mitigation:** store fresh baselines here, and don't quote the source numbers as this repo's results. The proposal names them only as motivation.
- **[Trade-off]** Five tasks instead of twelve cases cover less (DataDriver, localisation, World library). → These are recorded as follow-up candidates. The skill content for them is still checked by the structure and example tests.
- **[Risk]** The review grader can match keywords in the final message that the agent didn't mean as findings. → **Mitigation:** require the findings format from `review-checklist.md` (`ID — file:line — …`) and count only lines in that format.

## Migration Plan

This adds content only:
- Users of `rf-core` get `rf-bdd` with the next release after 5.0.0. Nothing is removed or renamed, so no installer migration is needed.
- Rollback is a revert of the PR, or pinning the marketplace to `v5.0.0`.

## Open Questions

- Whether a second maintainer for `rf-core` is available before the governance exemption expires (2027-01-31). This doesn't block this change, because the existing dated entry covers it.
