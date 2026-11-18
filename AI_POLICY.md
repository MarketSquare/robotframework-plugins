# AI and automated contributions

AI tools and coding agents are welcome here. Much of this repository is written with them, and what it ships (skills, hooks, subagents, scripts) is read and run by other people's agents.

How a change was produced doesn't matter. What matters is that a person then takes it over, understands it, and stays accountable for it through review, testing and follow-up.

This policy covers pull requests, issues, discussions, comments, review replies, documentation and generated files. It is adapted from [RobotCode's AI policy](https://github.com/robotcodedev/robotcode/blob/main/AI_POLICY.md), and it adds to [CONTRIBUTING.md](CONTRIBUTING.md); it doesn't replace it. [AGENTS.md](AGENTS.md) is the matching guide for the agents themselves.

## You are responsible for what you submit

Before you submit AI-assisted or automated work, make sure that:

- you understand it and can explain it in review;
- you have read all generated output yourself;
- you have run the checks in [CONTRIBUTING.md](CONTRIBUTING.md#checks-a-pr-must-pass) locally;
- issue reports and documentation are accurate and relevant;
- the change does one thing, without unrelated refactoring or generated filler;
- you will handle review feedback yourself.

Don't submit code, tests, documentation, reports or comments that you don't understand.

## Say when AI helped

If AI tools or agents did a substantial part of a pull request, issue or comment, say so where reviewers see it: in the PR description (the template has an "AI assistance" section), the issue body or the comment. One line is enough:

> AI assistance: prepared with `<tool>`. I reviewed the result, understand it, ran the checks locally, and have the right to submit it under the Apache-2.0 licence.

A commit trailer such as `AI-Assisted-By: <tool>` is welcome but optional. Grammar fixes, formatting and ordinary editor completions need no disclosure. Disclosing doesn't replace review, testing or your responsibility for the change.

## Licence and right to submit

By submitting, you confirm that you have the right to submit the content under the project's [Apache-2.0 licence](LICENSE), and that the tools you used impose no terms that conflict with it.

Treat generated output as untrusted. Leave it out if you can't tell where it came from, if it looks copied from third-party code, or if its licence is unclear. If it is based on third-party material, say which and under what licence.

The person who submits is the contributor of record, not the tool.

## Issues, comments and PR descriptions

AI can help you draft text, but read and edit it before you post. Explain in your own words what changed and why, how you tested it, or what problem you hit and how to reproduce it. Unreviewed generated text in an issue, PR or comment may be closed, with a request to resubmit with real context.

## Pull requests

AI-assisted PRs meet the same bar as any other:

- they follow [CONTRIBUTING.md](CONTRIBUTING.md) and pass its checks;
- they do one thing;
- generated files are regenerated with their command, not edited (see below);
- tests cover the behaviour, not only the shape of this diff;
- they don't leave investigation, integration or validation work for maintainers.

Small fixes are welcome when they are correct, focused and verified.

## In this repository

The output of this repository is itself agent content, so a few rules go further than RobotCode's:

- **Plugin content is security-relevant.** Skills, hooks, subagents and scripts are read and run by other people's agents. Every change to them goes through the security gate ([SECURITY.md](SECURITY.md)); treat a new hook, tool permission or network call as something a reviewer must look at, and say so in the PR.
- **Keywords must exist.** Every keyword a skill teaches has to resolve against the library it names, in the library version the plugin supports. `scripts/check-skill-keywords.py` checks this in CI.
- **Generated files aren't edited by hand.** `docs/catalog.md`, `.claude-plugin/marketplace.json`, the `version` in each `plugin.json`, `plugins/*/variants/` and the eval baselines are generated. Edit the source and name the command that regenerated them in the PR; [AGENTS.md](AGENTS.md#generated-files) lists the commands.
- **Paid eval runs are for maintainers.** Live eval runs and re-baselines cost money and are dispatched by maintainers. Ask for one in the PR instead.
- **Eval tasks read like real work.** Eval tasks and fixtures read like real user requests and real projects. They don't hint at what the grader checks.

## RobotCode first

The [`robotcode` CLI](https://robotcode.io/guides/cli/) is the core of the Robot Framework AI toolstack. AI solutions in this repository use it for running tests, discovering tests, static analysis, analysing results, running keywords step by step in the REPL, keyword and library documentation, and debugging. Use it instead of writing a new implementation of any of these.

When RobotCode can't do something a skill needs, report it or contribute it upstream at [robotcode](https://github.com/robotcodedev/robotcode), the central place for such improvements, rather than working around it here. A custom script that bridges the gap names the upstream issue in a comment.

Custom scripts are welcome for hook glue, skill helpers, eval grading and project conventions, as long as they call `robotcode` for the capabilities above instead of re-implementing them. In practice, re-implementing means our own code that parses Robot Framework files to resolve keywords, runs `robot` and parses `output.xml` to report results, or builds libdoc output to look up keywords, when a `robotcode` command gives the same answer. [AGENTS.md](AGENTS.md#robotcode-first) maps each capability to its command.

## Low-context submissions

Low-context, fully automated or unverified submissions may be closed. That includes submissions that:

- come from a quick scan of issues or code;
- ignore [CONTRIBUTING.md](CONTRIBUTING.md) or this policy;
- show no verification;
- make broad, unrelated or mechanical changes;
- add needless abstraction, boilerplate, comments or tests;
- misread how the plugins, the installer or the evals work;
- leave the investigation or validation to maintainers.

## How the policy is applied

Maintainers decide how this policy applies. They may ask for changes with a pointer to it, or close a PR, issue or comment that doesn't meet it. If you think a decision was wrong, say so on the same PR or issue and add the missing context. Disagreeing politely is fine; resubmitting the same low-context change is not.

The policy isn't meant to put off careful contributors. It keeps the plugins maintainable, and makes clear that the person submitting understands, verifies and cleans up automated output first.
