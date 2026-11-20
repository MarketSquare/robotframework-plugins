*** Settings ***
Documentation       Rule: late returns are fined per day.
Resource            reservation_steps.resource
Test Tags           rule:fine-per-day
Test Template       Returning "Dune" ${days} days late costs Mia ${fine} EUR


*** Test Cases ***                          DAYS    FINE
One day late costs 0.50 EUR                 1       0.50
A week late costs 3.50 EUR                  7       3.50
A month late costs 15.00 EUR                30      15.00
