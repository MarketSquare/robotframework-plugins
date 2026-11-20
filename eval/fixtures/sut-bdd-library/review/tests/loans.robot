*** Settings ***
Library             LibraryService
Resource            loan_steps.resource


*** Test Cases ***
Test loan 1
    Register Member    user1
    Add Book    book1    1
    Given user1 is registered and the library has book1
    When user1 opens the catalogue and selects book1 and presses borrow
    Then everything is fine

Check stuff
    Given Mia is a standard member
    And Noah is a standard member
    And the library has 1 copy of "Dune"
    When Mia borrows "Dune"
    Then the loan works
    When Noah borrows "Dune"
    Then the loan is refused with "No copy available"
