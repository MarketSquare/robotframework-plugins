---
name: rf-mind
description: "Use first for exact lookups in an RF test repo: tickets, keywords, callers, tags."
license: Apache-2.0
compatibility: Requires Python 3.10+ with robotframework 7 or later, and PyPI access once to install robotframework-mind. Reads the test repo on disk; no network calls.
metadata:
  author: ai94iq
---

# robotframework-mind Skill

## When to use

Use this skill when the question is about exact facts in a Robot Framework test repo: which tests carry a ticket key, where a keyword is defined, who calls a keyword, which tests have a tag, or where an endpoint path is used. Use it before grep or before reading whole suites. For writing or running Robot tests, use `rf-language` (plugin `rf-core`) or `rf-setup` (plugin `rf-core`) instead.

## Install

In the test repo's project:

```bash
uv add robotframework-mind
```

The package has no `robot_mind` command. Run it as a module:

```bash
python -m robot_mind --root <repo> <command> <term>
```

## Commands

| Command | Returns |
|---|---|
| `ticket KEY` | tests and keywords whose tags, name or doc mention the key |
| `kw NAME` | every definition of the keyword; case, spaces and underscores are ignored |
| `callers NAME` | each call site (keyword, test or suite fixture) with its line; falls back to substring when no exact name matches |
| `tag TAG` | tests with that tag; `role:*` matches every tag that starts with `role:` |
| `find TEXT` | names, tags, docs, args, variable values and JSON entries containing the text, then the keywords that use a matching variable |

Options, given before the command:

- `--root <repo>`: the test repo to search (required for any useful result)
- `--limit N`: cap the lines (default 20)
- `--json`: print the hits as a JSON array

## Read the output

Each text line is `kind  name  file:line`, then tags in brackets, or args and a doc after ` - `. Kinds seen: `test`, `keyword`, `var`, `json`, `suite setup`. A `callers` line also names the call line. With `--json`, each hit has `kind`, `name`, `file`, `line`, `tags`, `args`, `doc`, `value` and `call_line`.

Open the `file:line` before you edit anything; the index shows where a thing is, not its current meaning.

## Gotchas

- Exit code is 0 for a bad `--root` and for no match. A missing repo prints `no match` too, so check the output text, not the exit code.
- On Git Bash (Windows), a term that starts with `/` is rewritten into a Windows path and matches nothing. Run with `MSYS_NO_PATHCONV=1` set for that command, for example `MSYS_NO_PATHCONV=1 python -m robot_mind --root <repo> find /api/items/query`.
- `tag` takes the exact tag or a `prefix:*` glob. A bare `role:` matches nothing.
- The index lives in `~/.cache/robotframework-mind/`, never in the repo. Files ignored by `.gitignore` are not searched. Files over 5 MB (docs JSON) or 50 MB (`.robot`, `.resource`) are skipped.
- Output is capped by `--limit` (default 20). Raise it before concluding that nothing else exists.

## Workflow

1. Start with the narrowest command: `ticket` for a Jira key, `kw` for a keyword name, `tag` for a tag, `find` for free text or an endpoint.
2. For a keyword, run `kw` first to find the definition, then `callers` to see where it is used.
3. Raise `--limit` only when the first result is full.
4. Use `--json` when a script reads the result.
5. Confirm each hit by opening its `file:line`.

## Companion Skills

| Need | Skill |
|------|-------|
| Install Robot Framework or a library, fix the environment | `rf-setup` (plugin `rf-core`) |
| Write tests, suites, user keywords, resources and variables in Robot Framework syntax | `rf-language` (plugin `rf-core`) |
