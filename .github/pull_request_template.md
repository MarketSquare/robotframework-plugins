## What this changes

<!-- One or two sentences: what a user of the plugin gets from this PR. -->

## AI assistance

<!-- Did an AI tool or agent do a substantial part of this? Name it and confirm
     you reviewed the result, ran the checks and have the right to submit it
     (AI_POLICY.md). Grammar fixes and editor completions don't count.
     Otherwise write "none". -->

## Before you open it

- Robot Framework capabilities go through `robotcode`; gaps are reported upstream ([AGENTS.md](../AGENTS.md#robotcode-first)).
- Generated files were regenerated with their command, not edited by hand.

## Checked by CI

These run on every PR and must pass before it can merge. You don't need to tick anything.

- **Security gate result:** house content rules, the scanners on each changed plugin against its baseline, and secrets in the diff.
- **Validate plugin structure:** the catalogue, docs voice, tier evidence, manifests and SKILL.md frontmatter.
- **Check generated variants and plugin layout:** per-agent variants, skill names, symlinks and no plugin MCP server.
- **Check library-skill keywords:** every keyword a library skill teaches exists and isn't deprecated.
- **Validate .robot examples:** dry runs of the examples.
- **Validate SKILL.md frontmatter (agentskills.io)**, **Lint**, **Test** and **Template plugin passes the PR checks**.

## For the reviewer

<!-- Anything the checks can't see: a behaviour change, a new tool permission
     or allowed-tools entry, a new hook, a judgement call. Write "nothing" if
     there is none. If the PR changes a plugin, mention its catalog.yaml
     maintainers here. -->
