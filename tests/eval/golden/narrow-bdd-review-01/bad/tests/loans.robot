*** Settings ***
Documentation       As a library member
...                 I want to borrow books
...                 So that I can read them at home
Metadata            Feature    Borrowing books
Resource            loan_steps.resource
Test Tags           feature:borrowing-books


*** Test Cases ***
Member borrows the last copy
    Given Mia is a standard member
    And the library has 1 copy of "Dune"
    When Mia borrows "Dune"
    Then the loan works

Second member finds no copy
    Given Mia is a standard member
    And Noah is a standard member
    And the library has 1 copy of "Dune"
    And Mia borrows "Dune"
    When Noah borrows "Dune"
    Then the loan is refused with "No copy available"
