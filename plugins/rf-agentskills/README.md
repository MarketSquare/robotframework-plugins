# rf-agentskills bundle

Installs every Robot Framework plugin of this marketplace at once: `rf-core`, `rf-web`, `rf-api`, `rf-mobile` and `rf-desktop`. It has no content of its own. Install instructions for every agent are in the [repository README](https://github.com/MarketSquare/robotframework-plugins#install).

## Install

```
/plugin install rf-agentskills --marketplace MarketSquare/robotframework-plugins
```

That one step works on Claude Code 2.1.275 or later. The commands for other agents and older versions are in the repository README.

Until 3.0.0 this plugin held all nine skills, three subagents and the hooks. From 4.0.0 they are maintained in the five plugins above, so a web team can install `rf-core` and `rf-web` only. `rf-agentskills` ships a copy of all five, generated from them for each release. Projects that enable `rf-agentskills@robotframework-plugins` keep everything, under the same `rf-agentskills:` prefix as before.

| Plugin | Skills and subagents |
|---|---|
| `rf-core` | `rf-language`, `rf-setup`, `rf-python-library`; `rf-test-architect`, `rf-debug-expert`, `rf-migration-guide`; all hooks |
| `rf-web` | `rf-browser`, `rf-selenium` |
| `rf-api` | `rf-requests`, `rf-restinstance` |
| `rf-mobile` | `rf-appium` |
| `rf-desktop` | `rf-platynui` |

## Bundle or separate plugins, not both

Install either this bundle or the plugins you need. With both, each skill appears twice, once as `rf-agentskills:rf-browser` and once as `rf-web:rf-browser`. Moving from the bundle to separate plugins changes the skill prefixes, so update project instructions or docs that name a prefixed skill.

robotcode is a prerequisite of `rf-core`; see its README.
