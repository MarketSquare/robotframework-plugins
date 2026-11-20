*** Settings ***
Documentation    Smoke test for the Demo Login Android app (see app/SCREENS.md).
...              Needs the Maestro CLI and a running emulator.
Library          MaestroLibrary    timeout=10s
Suite Teardown   Close All Applications


*** Test Cases ***
App Starts On The Login Screen
    [Tags]    smoke
    Open Application    com.example.demologin
    Wait Until Element Is Visible    id=com.example.demologin:id/username
