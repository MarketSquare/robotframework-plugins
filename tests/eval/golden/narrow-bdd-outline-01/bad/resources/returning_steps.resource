*** Settings ***
Library             LibraryService


*** Keywords ***
Return late
    [Arguments]    ${days}    ${fine}
    Register Member    Mia
    Add Book    Dune    1
    Borrow    Mia    Dune
    ${day}    Evaluate    datetime.date(2026, 12, 3) + datetime.timedelta(days=${days})
    Set Today    ${day}
    ${charged}    Return Book    Mia    Dune
    Should Be Equal As Numbers    ${charged}    ${fine}
