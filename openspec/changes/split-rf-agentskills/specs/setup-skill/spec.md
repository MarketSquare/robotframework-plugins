## MODIFIED Requirements

### Requirement: Library-specific post-install steps are documented

The skill SHALL keep a library table with one row per library that a catalogue plugin covers. Each row SHALL give the package name, the install command in uv form, a one-line summary of any step needed after installing the Python package, and the library skill and plugin that own the full steps:
- Browser: `[bb]` BrowserBatteries with `rfbrowser install`, or Node.js LTS with `rfbrowser init` (`rf-browser`, plugin `rf-web`);
- SeleniumLibrary: Selenium Manager resolves drivers (`rf-selenium`, plugin `rf-web`);
- AppiumLibrary: Appium server and platform drivers via npm (`rf-appium`, plugin `rf-mobile`);
- RequestsLibrary (`rf-requests`, plugin `rf-api`);
- RESTinstance (`rf-restinstance`, plugin `rf-api`);
- PlatynUI: pre-release install (`rf-platynui`, plugin `rf-desktop`).

The full post-install steps SHALL live in the library skills, not in `rf-setup`. robotcode is covered by the prerequisite step, not by this table. Robocop comes with `robotcode[all]` and SHALL NOT be listed as a separate install.

#### Scenario: Browser has both install paths
- **WHEN** rf-setup's library table and `references/install.md` of rf-browser are read
- **THEN** the table row names both paths in one line, and the rf-browser reference shows the no-Node path (`robotframework-browser[bb]` then `rfbrowser install`), the Node path (Node 22/24/26 LTS, `robotframework-browser`, then `rfbrowser init`) and the `python -m Browser.entry` fallback when `rfbrowser` is not found

#### Scenario: Library skills linked
- **WHEN** the library table in `SKILL.md` is read
- **THEN** each library row names its companion skill and that skill's plugin, and no row names `rf-robotcode`
