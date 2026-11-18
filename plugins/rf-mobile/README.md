# rf-mobile plugin

Robot Framework skills for mobile tests. Install instructions for every agent are in the [repository README](https://github.com/MarketSquare/robotframework-plugins#install).

## Install

```
/plugin install rf-mobile --marketplace MarketSquare/robotframework-plugins
```

That one step works on Claude Code 2.1.275 or later. The commands for other agents and older versions are in the repository README.

| Skill | Library and package |
|---|---|
| `rf-appium` | AppiumLibrary: `robotframework-appiumlibrary` |

## Needs rf-core

This plugin depends on `rf-core`, which holds Robot Framework syntax, environment setup, the subagents and the validation hooks. Claude Code installs `rf-core` with it. Copilot CLI and Codex don't install plugin dependencies, so install `rf-core` there too:

```bash
copilot plugin install rf-core@robotframework-plugins
codex plugin add rf-core@robotframework-plugins
```

The `robotframework-plugins` installer adds `rf-core` for you.

Changes: [CHANGELOG.md](../../CHANGELOG.md) at the repository root.
