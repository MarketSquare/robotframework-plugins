*** Settings ***
Documentation     Android smoke test with MaestroLibrary. Needs a running emulator and the Maestro CLI.
Library           MaestroLibrary    timeout=10s
Suite Teardown    Close All Applications

*** Test Cases ***
Search Settings Finds Wi-Fi
    Open Application    com.android.settings
    Expect Element      text=Search settings    visible
    Click Text          Search settings    exact_match=True
    Input Text          id=com.google.android.settings.intelligence:id/open_search_view_edit_text    wifi
    Wait Until Page Contains    Wi-Fi
    [Teardown]    Close Application
