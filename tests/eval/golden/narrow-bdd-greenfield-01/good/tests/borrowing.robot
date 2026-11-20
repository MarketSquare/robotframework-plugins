*** Settings ***
Documentation       As a library member
...                 I want to borrow books
...                 So that I can read them at home
Metadata            Feature    Borrowing books
Resource            borrowing_steps.resource
Test Tags           feature:borrowing-books


*** Test Cases ***
Member borrows an available book for 21 days
    [Documentation]    Rule: an available copy is lent for 21 days.
    [Tags]    rule:loan-period
    Given the library has 2 copies of "Dune"
    And Mia is a standard member
    When Mia borrows "Dune"
    Then the loan is granted until 2026-12-03

Book without an available copy cannot be borrowed
    [Documentation]    Rule: a book can only be lent while a copy is on the shelf.
    [Tags]    rule:copy-available
    Given the library has 0 copies of "Dune"
    And Mia is a standard member
    When Mia borrows "Dune"
    Then the loan is refused with "No copy available"

Standard member borrows a third book
    [Documentation]    Rule: standard members may have 3 books at a time.
    [Tags]    rule:loan-limit
    Given Mia is a standard member
    And Mia has 2 books on loan
    And the library has a copy of "Dune"
    When Mia borrows "Dune"
    Then the loan is granted until 2026-12-03

Standard member with 3 books cannot borrow a fourth
    [Documentation]    Rule: standard members may have 3 books at a time.
    [Tags]    rule:loan-limit
    Given Mia is a standard member
    And Mia has 3 books on loan
    And the library has a copy of "Dune"
    When Mia borrows "Dune"
    Then the loan is refused with "Loan limit reached"

Premium member with 10 books cannot borrow an eleventh
    [Documentation]    Rule: premium members may have 10 books at a time.
    [Tags]    rule:loan-limit
    Given Noah is a premium member
    And Noah has 10 books on loan
    And the library has a copy of "Dune"
    When Noah borrows "Dune"
    Then the loan is refused with "Loan limit reached"

Blocked member cannot borrow
    [Documentation]    Rule: blocked members cannot borrow.
    [Tags]    rule:blocked-member
    Given Mia is a standard member
    And Mia is blocked
    And the library has a copy of "Dune"
    When Mia borrows "Dune"
    Then the loan is refused with "Member is blocked"

Member with unpaid fines cannot borrow
    [Documentation]    Rule: members with unpaid fines cannot borrow.
    [Tags]    rule:unpaid-fines
    Given Mia is a standard member
    And Mia has unpaid fines of 2.50 EUR
    And the library has a copy of "Dune"
    When Mia borrows "Dune"
    Then the loan is refused with "Unpaid fines"
