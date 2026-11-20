*** Settings ***
Documentation       As a library member
...                 I want to borrow books
...                 So that I can read them at home
Metadata            Feature    Borrowing books
Resource            borrowing_steps.resource
Test Tags           feature:borrowing-books


*** Test Cases ***
Member borrows an available book
    [Documentation]    Rule: an available copy is lent for 21 days.
    [Tags]    rule:loan-period
    Given the library has 2 copies of "Dune"
    And Mia is a standard member
    When Mia borrows "Dune"
    Then the loan is granted until 2026-12-03
    And Mia has "Dune" on loan

Book without an available copy cannot be borrowed
    [Documentation]    Rule: a book can only be lent while a copy is on the shelf.
    [Tags]    rule:copy-available
    Given the library has 0 copies of "Dune"
    And Mia is a standard member
    When Mia borrows "Dune"
    Then the loan is refused with "No copy available"

Standard member with 3 books cannot borrow a fourth
    [Documentation]    Rule: standard members may have 3 books at a time.
    [Tags]    rule:loan-limit
    Given the library has 2 copies of "Dune"
    And Mia is a standard member
    And Mia has 3 books on loan
    When Mia borrows "Dune"
    Then the loan is refused with "Loan limit reached"

Premium member borrows beyond the standard limit
    [Documentation]    Rule: premium members may have 10 books at a time.
    [Tags]    rule:loan-limit
    Given the library has 2 copies of "Dune"
    And Noah is a premium member
    And Noah has 9 books on loan
    When Noah borrows "Dune"
    Then the loan is granted until 2026-12-03

Premium member with 10 books cannot borrow an eleventh
    [Documentation]    Rule: premium members may have 10 books at a time.
    [Tags]    rule:loan-limit
    Given the library has 2 copies of "Dune"
    And Noah is a premium member
    And Noah has 10 books on loan
    When Noah borrows "Dune"
    Then the loan is refused with "Loan limit reached"

Blocked member cannot borrow
    [Documentation]    Rule: blocked members cannot borrow at all.
    [Tags]    rule:blocked-member
    Given the library has 2 copies of "Dune"
    And Mia is a standard member
    And Mia is blocked
    When Mia borrows "Dune"
    Then the loan is refused with "Member is blocked"
