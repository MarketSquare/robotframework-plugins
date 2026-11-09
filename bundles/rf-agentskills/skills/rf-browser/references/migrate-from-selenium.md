# Migrating from SeleniumLibrary to Browser

A keyword map for moving suites from SeleniumLibrary to Browser Library. Verify each replacement with `robotcode doc keyword <Library> "<Keyword>"` before you use it; argument orders differ.

| SeleniumLibrary | Browser | Note |
|---|---|---|
| `Open Browser    ${URL}    chrome` | `New Browser    chromium` + `New Page    ${URL}` | browser → context → page |
| `Close All Browsers` | `Close Browser    ALL` | |
| `Input Text` / `Input Password` | `Fill Text` / `Fill Secret` | `Fill Secret` takes `$var` |
| `Click Element    css=x` | `Click    x` | CSS is the default strategy |
| `Wait Until Element Is Visible` | usually none (auto-wait), else `Wait For Elements State    x    visible` | |
| `Wait Until Page Contains    t` | `Get Text    sel    contains    t` | assertion engine |
| `Select From List By Value` | `Select Options By    sel    value    v` | argument order |
| `Get Value    id=x` | `Get Property    id=x    value` | |
| `Execute Javascript` | `Evaluate JavaScript` | |
| `Select Frame    id=x` | selector `id=x >>> inner` | no frame switching |
| `Capture Page Screenshot` | `Take Screenshot` | |

Phases: import both libraries during the transition, move shared login and navigation
keywords first, then suites one by one, and remove the SeleniumLibrary import last.

After each file, check it with `robotcode analyze code` and run the affected tests by longname (`robotcode robot -bl "<Suite.Test>"`). The `rf-migration-guide` subagent (plugin `rf-core`) runs the phased migration and reports each file as migrated or unverified.
