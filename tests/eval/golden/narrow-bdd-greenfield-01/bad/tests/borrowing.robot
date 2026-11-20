*** Settings ***
Library             LibraryService


*** Test Cases ***
Borrow available book
    Given the library has a copy of "Dune"
    And Mia is a standard member
    ${loan}    Borrow    Mia    Dune
    Then Should Be Equal    ${loan}[status]    lent

No copy available
    Register Member    Mia
    ${loan}    Borrow    Mia    Dune
    Should Be Equal    ${loan}[reason]    No copy available

Loan limit standard
    Register Member    Mia
    FOR    ${n}    IN RANGE    3
        Add Book    Book ${n}
        Borrow    Mia    Book ${n}
    END
    Add Book    Dune
    ${loan}    Borrow    Mia    Dune
    Should Be Equal    ${loan}[reason]    Loan limit reached

Blocked member
    Register Member    Mia
    Block Member    Mia
    Add Book    Dune
    ${loan}    Borrow    Mia    Dune
    Should Be Equal    ${loan}[reason]    Member is blocked

Unpaid fines
    Register Member    Mia
    Add Fine    Mia    1
    Add Book    Dune
    ${loan}    Borrow    Mia    Dune
    Should Be Equal    ${loan}[reason]    Unpaid fines


*** Keywords ***
The library has a copy of "${title}"
    Add Book    ${title}    1

${member} is a standard member
    Register Member    ${member}
