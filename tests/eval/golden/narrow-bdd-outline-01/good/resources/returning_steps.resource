*** Settings ***
Documentation       Step keywords for returning books.
Library             LibraryService


*** Variables ***
${DUE_DATE}         2026-12-03
${LAST_FINE}        ${None}


*** Keywords ***
${member} has borrowed "${title}"
    [Documentation]    Lends ``title`` to ``member`` today; the loan is due on ${DUE_DATE}.
    Register Member    ${member}
    Add Book    ${title}    1
    ${loan}    Borrow    ${member}    ${title}
    Should Be Equal As Strings    ${loan}[due_date]    ${DUE_DATE}

${member} returns "${title}" on the due date
    [Documentation]    ``member`` returns ``title`` on its due date.
    Return On Day    ${member}    ${title}    ${DUE_DATE}

${member} returns "${title}" one day late
    [Documentation]    ``member`` returns ``title`` the day after its due date.
    Return Days Late    ${member}    ${title}    1

${member} returns "${title}" ${days: int} days late
    [Documentation]    ``member`` returns ``title`` ``days`` days after its due date.
    Return Days Late    ${member}    ${title}    ${days}

${member} is charged a fine of ${fine} EUR
    [Documentation]    The last return cost ``fine`` EUR.
    Should Be Equal As Numbers    ${LAST_FINE}    ${fine}

${member} is charged no fine
    [Documentation]    The last return cost nothing.
    Should Be Equal As Numbers    ${LAST_FINE}    0

A late return of ${days: int} days costs ${fine} EUR
    [Documentation]    Outline: Mia returns "Dune" ``days`` days late and pays ``fine`` EUR.
    Given Mia has borrowed "Dune"
    When Mia returns "Dune" ${days} days late
    Then Mia is charged a fine of ${fine} EUR

Return Days Late
    [Documentation]    Returns ``title`` ``days`` days after the due date.
    [Arguments]    ${member}    ${title}    ${days}
    [Tags]    robot:private
    ${day}    Evaluate    datetime.date.fromisoformat($DUE_DATE) + datetime.timedelta(days=${days})
    Return On Day    ${member}    ${title}    ${day}

Return On Day
    [Documentation]    Returns ``title`` on ``day``.
    [Arguments]    ${member}    ${title}    ${day}
    [Tags]    robot:private
    Set Today    ${day}
    ${fine}    Return Book    ${member}    ${title}
    VAR    ${LAST_FINE}    ${fine}    scope=TEST
