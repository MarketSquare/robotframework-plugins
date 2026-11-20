*** Settings ***
Documentation       Rule: reservations are served first come, first served.
Resource            reservation_steps.resource
Test Tags           rule:first-come-first-served


*** Test Cases ***
The returned copy is held for the first member in the queue
    Given Noah has reserved "Dune"
    And Lea has reserved "Dune"
    When Mia returns "Dune"
    Then Noah can borrow "Dune"
    But Lea cannot borrow "Dune"
