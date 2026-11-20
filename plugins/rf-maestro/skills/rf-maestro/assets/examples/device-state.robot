*** Settings ***
Documentation     Device state set inside a test and put back in its teardown.
Library           MaestroLibrary    timeout=10s
Suite Teardown    Close All Applications

*** Test Cases ***
Chart Shows In Landscape
    [Documentation]    Turns the device, checks the layout, then turns it back.
    [Teardown]    Run Keywords    Portrait    AND    Close Application
    Open Application    com.example.app
    Set Application Permissions    camera=deny    all=allow
    Landscape
    Wait Until Element Is Visible    id=chart_view
    Capture Page Screenshot    chart-landscape.jpg

Location Changes The Store List
    [Documentation]    Sets a location, then checks the store list for it.
    [Teardown]    Close Application
    Open Application    com.example.app
    Set Location    52.5200    13.4050
    Wait Until Page Contains    Berlin

Dark Mode Layout Matches Reference
    [Documentation]    Compares the home screen with a reference image in dark mode.
    [Teardown]    Run Keywords    Set Dark Mode    ${False}    AND    Close Application
    Open Application    com.example.app
    Set Dark Mode    ${True}
    Wait Until Page Contains Element    id=home_root
    Screenshot Should Match    ${CURDIR}/references/home-dark.png    threshold=95    locator=id=home_root
