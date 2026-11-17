*** Settings ***
Documentation    Smoke test that proves the fixture's robot runner works.
Resource         ../resources/common.resource


*** Test Cases ***
Fixture Smoke Test
    [Documentation]    Trivially passing test to confirm the environment.
    [Tags]    smoke
    ${greeting}=    Build Greeting    World
    Should Be Equal    ${greeting}    Hello, World
