*** Settings ***
Documentation       Step keywords for reservations and returns.
Library             LibraryService


*** Variables ***
${DUE_DATE}         2026-12-03
${LAST_LOAN}        ${None}
${LAST_FINE}        ${None}


*** Keywords ***
The only copy of "${title}" is on loan to ${member}
    [Documentation]    The library owns one copy of ``title``, and ``member`` has borrowed it.
    Add Book    ${title}    1
    Register Member    ${member}
    ${loan}    Borrow    ${member}    ${title}
    Should Be Equal    ${loan}[status]    lent

${member} has reserved "${title}"
    [Documentation]    Registers ``member`` and puts them in the queue for ``title``.
    Register Member    ${member}
    Reserve    ${member}    ${title}

${member} returns "${title}"
    [Documentation]    ``member`` returns ``title`` today.
    ${fine}    Return Book    ${member}    ${title}
    VAR    ${LAST_FINE}    ${fine}    scope=TEST

${member} returns "${title}" ${days: int} days after the due date
    [Documentation]    ``member`` returns ``title`` ``days`` days after its due date.
    Return Late    ${member}    ${title}    ${days}

${member} returns "${title}" one day after the due date
    [Documentation]    ``member`` returns ``title`` the day after its due date.
    Return Late    ${member}    ${title}    1

${member} can borrow "${title}"
    [Documentation]    ``member`` asks for ``title`` and gets it.
    ${loan}    Borrow    ${member}    ${title}
    Should Be Equal    ${loan}[status]    lent    msg=Loan refused: ${loan}[reason]    values=False

${member} cannot borrow "${title}"
    [Documentation]    ``member`` asks for ``title`` and is refused.
    ${loan}    Borrow    ${member}    ${title}
    Should Be Equal    ${loan}[status]    refused

${member} is charged a fine of ${fine} EUR
    [Documentation]    The last return cost ``member`` ``fine`` EUR.
    Should Be Equal As Numbers    ${LAST_FINE}    ${fine}

Returning "${title}" ${days: int} days late costs ${member} ${fine} EUR
    [Documentation]    Outline: ``member`` returns ``title`` ``days`` days late and pays ``fine`` EUR.
    When ${member} returns "${title}" ${days} days after the due date
    Then ${member} is charged a fine of ${fine} EUR

Return Late
    [Documentation]    Returns ``title`` ``days`` days after the due date.
    [Arguments]    ${member}    ${title}    ${days}
    [Tags]    robot:private
    ${day}    Evaluate    datetime.date.fromisoformat($DUE_DATE) + datetime.timedelta(days=${days})
    Set Today    ${day}
    ${fine}    Return Book    ${member}    ${title}
    VAR    ${LAST_FINE}    ${fine}    scope=TEST
