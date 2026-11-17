*** Settings ***
Documentation    Smoke test: the Calculator window is present (see README.md).
...              Needs a desktop session with Calculator running.
Library          PlatynUI.BareMetal


*** Variables ***
${CALCULATOR}    //control:Window[@Name='Calculator']


*** Test Cases ***
Calculator Window Is Present
    [Tags]    smoke
    ${window}=    Query    ${CALCULATOR}    only_first=${True}
    Should Not Be Equal    ${window}    ${None}
