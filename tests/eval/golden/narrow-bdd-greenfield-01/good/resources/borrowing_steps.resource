*** Settings ***
Documentation       Step keywords for borrowing books.
Library             LibraryService


*** Variables ***
${LAST_LOAN}        ${None}


*** Keywords ***
The library has ${copies: int} copies of "${title}"
    [Documentation]    Puts ``copies`` copies of ``title`` on the shelf.
    Add Book    ${title}    ${copies}

The library has a copy of "${title}"
    [Documentation]    Puts one copy of ``title`` on the shelf.
    Add Book    ${title}    1

${member} is a ${membership:standard|premium} member
    [Documentation]    Registers ``member`` with a standard or premium membership.
    Register Member    ${member}    ${membership}

${member} is blocked
    [Documentation]    Blocks ``member``'s account.
    Block Member    ${member}

${member} has unpaid fines of ${amount} EUR
    [Documentation]    Adds an unpaid fine of ``amount`` EUR to ``member``'s account.
    Add Fine    ${member}    ${amount}

${member} has ${count: int} books on loan
    [Documentation]    Lends ``count`` different books to ``member``.
    FOR    ${n}    IN RANGE    1    ${count + 1}
        Add Book    Book ${n}    1
        ${loan}    Borrow    ${member}    Book ${n}
        Should Be Equal    ${loan}[status]    lent
    END

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
