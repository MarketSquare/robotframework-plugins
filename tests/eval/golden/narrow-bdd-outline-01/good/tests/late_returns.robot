*** Settings ***
Documentation       As the library
...                 I want late returns to be fined per day
...                 So that books come back on time
...
...                 Rule: a late return costs 0.50 EUR per day; a return on the due date is free.
Metadata            Feature    Late return fines
Resource            returning_steps.resource
Test Tags           feature:late-return-fines    rule:fine-per-day
Test Template       A late return of ${days} days costs ${fine} EUR


*** Test Cases ***                          DAYS    FINE
A week late costs a week of fines           7       3.50
A month late costs thirty days of fines     30      15.00

Return on the due date is free
    [Template]    NONE
    Given Mia has borrowed "Dune"
    When Mia returns "Dune" on the due date
    Then Mia is charged no fine

One day late costs one day of fines
    [Template]    NONE
    Given Mia has borrowed "Dune"
    When Mia returns "Dune" one day late
    Then Mia is charged a fine of 0.50 EUR
