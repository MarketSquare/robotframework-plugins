## What this changes

<!-- One or two sentences: what a user of the plugin gets from this PR. -->

<!-- ai-disclosure: the AI assistance line goes here (change ai-contributor-docs). -->

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
