## MODIFIED Requirements

### Requirement: Library skills defer installation to rf-setup

Each library skill (rf-browser, rf-selenium, rf-appium, rf-requests, rf-restinstance, rf-platynui) SHALL own its library's installation guidance, because it ships in a different plugin from `rf-setup`. Its `SKILL.md` SHALL keep that guidance to one short block with three parts:
- a pointer to the `rf-setup` skill (plugin `rf-core`) for environment creation, other installers (venv + pip, Poetry) and troubleshooting;
- the library's install command in uv form;
- the library-specific post-install essential, for example `rfbrowser install` or the Appium drivers.

Longer post-install steps SHALL live in the skill's own `references/install.md`. The skill SHALL also name `rf-setup` in its companion-skills section. `rf-setup`'s library table SHALL show the same uv command for each library.

#### Scenario: Pointer and uv line present
- **WHEN** a library skill's `SKILL.md` installation block is read
- **THEN** it names `rf-setup` and its plugin `rf-core` as the place for environment setup, pip/Poetry forms and troubleshooting
- **AND** it contains the library's `uv add …` command, identical to the one in rf-setup's library table

#### Scenario: Post-install essential matches rf-setup
- **WHEN** the rf-appium installation block is read
- **THEN** it states that the Appium server and platform drivers are installed with npm (`appium driver install uiautomator2` / `xcuitest`), and `references/install.md` of rf-appium gives the full steps
- **WHEN** the rf-restinstance installation block is read
- **THEN** it states the Python ≥ 3.11 floor

#### Scenario: Companion section links setup
- **WHEN** a library skill's companion-skills section is read
- **THEN** it lists `rf-setup` (plugin `rf-core`) for creating the project environment
