*** Settings ***
Documentation       Scenario Outline: the balance that remains after a withdrawal.
...
...                 Rule: a dispensed withdrawal is debited from the balance.
Resource            cash_withdrawal_steps.resource
Test Tags           rule:debit-on-dispense
Test Template       Withdrawing ${amount} EUR from a balance of ${balance} EUR leaves ${rest} EUR


*** Test Cases ***                  AMOUNT    BALANCE    REST
Partial withdrawal                  20        100        80
Withdrawal of the whole balance     100       100        0
Withdrawal of a single note         10        250        240


*** Keywords ***
Withdrawing ${amount} EUR from a balance of ${balance} EUR leaves ${rest} EUR
    [Documentation]    One example of the remaining-balance outline.
    Given Alice has a balance of ${balance} EUR
    When Alice withdraws ${amount} EUR
    Then the ATM dispenses ${amount} EUR
    And Alice's balance is ${rest} EUR
