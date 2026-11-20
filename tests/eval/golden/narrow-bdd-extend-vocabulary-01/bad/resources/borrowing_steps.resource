*** Settings ***
Documentation       Step definitions for borrowing books.
Library             LibraryService


*** Variables ***
${LAST_LOAN}        ${None}


*** Keywords ***
The library has ${copies: int} copies of "${title}"
    [Documentation]    Puts ``copies`` copies of ``title`` on the shelf.
    Add Book    ${title}    ${copies}

${member} is a ${membership:standard|premium} member
    [Documentation]    Registers ``member`` with a standard or premium membership.
    Register Member    ${member}    ${membership}

${member} borrows "${title}"
    [Documentation]    ``member`` asks to borrow ``title`` today.
    ${result}    Borrow    ${member}    ${title}
    VAR    ${LAST_LOAN}    ${result}    scope=TEST

The loan is granted until ${due}
    [Documentation]    The last loan was granted and is due on ``due`` (YYYY-MM-DD).
    Should Be Equal    ${LAST_LOAN}[status]    lent
    ...    msg=Expected the loan to be granted, but it was refused: ${LAST_LOAN}[reason]    values=False
    Should Be Equal As Strings    ${LAST_LOAN}[due_date]    ${due}

The loan is refused with "${reason}"
    [Documentation]    The last loan was refused, and the library gave ``reason``.
    Should Be Equal    ${LAST_LOAN}[status]    refused
    Should Be Equal    ${LAST_LOAN}[reason]    ${reason}

${member} has "${title}" on loan
    [Documentation]    ``title`` is among the books ``member`` currently has on loan.
    ${loans}    Get Loans    ${member}
    Should Contain    ${loans}    ${title}

${membership:standard|premium} member ${member} already has ${count: int} books
    Register Member    ${member}    ${membership}
    FOR    ${n}    IN RANGE    ${count}
        Add Book    Book ${n}    1
        Borrow    ${member}    Book ${n}
    END

Blocked member ${member}
    Register Member    ${member}
    Block Member    ${member}

${member} tries to borrow another book
    Add Book    Another Book    1
    ${result}    Borrow    ${member}    Another Book
    VAR    ${LAST_LOAN}    ${result}    scope=TEST

The request is rejected because "${reason}"
    Should Be Equal    ${LAST_LOAN}[reason]    ${reason}
