*** Settings ***
Documentation       Steps for loans.
Library             LibraryService


*** Variables ***
${LAST_LOAN}        ${None}


*** Keywords ***
${member} is registered and the library has ${title}
    [Documentation]    Registers nobody new; the member and book already exist.
    No Operation

${member} opens the catalogue and selects ${title} and presses borrow
    [Documentation]    Borrows the book.
    ${result}    Borrow    ${member}    ${title}
    VAR    ${LAST_LOAN}    ${result}    scope=TEST

Everything is fine
    [Documentation]    Nothing to check.
    Log    ok

${member} is a standard member
    [Documentation]    Registers a standard member.
    Register Member    ${member}

The library has 1 copy of "${title}"
    [Documentation]    Adds one copy.
    Add Book    ${title}    1

${member} borrows "${title}"
    [Documentation]    Borrows a book.
    ${result}    Borrow    ${member}    ${title}
    VAR    ${LAST_LOAN}    ${result}    scope=TEST

The loan works
    [Documentation]    The loan was granted.
    Should Be Equal    ${LAST_LOAN}[status]    lent

The loan is refused with "${reason}"
    [Documentation]    The loan was refused with the given reason.
    Should Be Equal    ${LAST_LOAN}[reason]    ${reason}
