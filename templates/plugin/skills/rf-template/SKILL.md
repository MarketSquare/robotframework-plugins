---
name: rf-template
description: "Use for RF tests that log a message (template skill). Replace with what yours covers and when to load it."
license: Apache-2.0
compatibility: Requires robotframework>=7 in the project environment.
metadata:
  author: your-github-handle
  version: "0.1.0"
---

# Template skill

Replace this skill with yours. Keep the shape: when to use it, the steps, where the details are, and the skills next to it.

## When to use

Load this skill when the user asks for a Robot Framework test that logs a message.

## Steps

1. Create `tests/example.robot` with one test case.
2. Use the `Log` keyword from BuiltIn to write the message.
3. Run the test: `uv run robot tests/example.robot`.

A complete example is in `assets/examples/example.robot`. More detail is in [references/usage.md](references/usage.md).

## Companion Skills

| Need | Skill |
|------|-------|
| Write tests, suites, user keywords, resources and variables in Robot Framework syntax | `rf-language` (plugin `rf-core`) |
| Install Robot Framework or a library, fix the environment | `rf-setup` (plugin `rf-core`) |
