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

Loan limit for standard members
    [Documentation]    Rule: standard members may have 3 books at a time.
    [Tags]    rule:loan-limit
    Given standard member Mia already has 3 books
    When Mia tries to borrow another book
    Then the request is rejected because "Loan limit reached"

Loan limit for premium members
    [Documentation]    Rule: premium members may have 10 books at a time.
    [Tags]    rule:loan-limit
    Given premium member Noah already has 10 books
    When Noah tries to borrow another book
    Then the request is rejected because "Loan limit reached"

Blocked members cannot borrow
    [Documentation]    Rule: blocked members cannot borrow at all.
    [Tags]    rule:blocked-member
    Given blocked member Mia
    When Mia tries to borrow another book
    Then the request is rejected because "Member is blocked"
