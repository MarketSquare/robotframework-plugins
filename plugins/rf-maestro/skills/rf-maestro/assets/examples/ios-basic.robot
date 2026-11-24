*** Settings ***
Documentation     iOS simulator smoke test with MaestroLibrary. Needs macOS, Xcode, a booted simulator and the Maestro CLI.
Library           MaestroLibrary    timeout=10s
Suite Setup       Open Application    com.example.app    clear_state=True
Suite Teardown    Close All Applications

*** Variables ***
${USER_NAME}    %{APP_USER=change-me}
${PASSWORD}    %{APP_PASSWORD=change-me}

*** Test Cases ***
Sign In Form Accepts Input
    Wait Until Page Contains Element    id=email_field
    Input Text                          id=email_field    ${USER_NAME}
    Input Password                      id=password_field    ${PASSWORD}
    Hide Keyboard                       key_name=Done
    Expect Element                      id=sign_in_button    enabled
