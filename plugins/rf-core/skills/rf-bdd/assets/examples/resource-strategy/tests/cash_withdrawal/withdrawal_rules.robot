*** Settings ***
Documentation       Rules that decide whether a withdrawal is dispensed.
Resource            cash_withdrawal_steps.resource


*** Test Cases ***
Account holder withdraws cash within their balance
    [Documentation]    Rule: a withdrawal within the balance is dispensed and debited.
    [Tags]    rule:debit-on-dispense    smoke
    Given Alice has a balance of 100 EUR
    When Alice withdraws 20 EUR
    Then the ATM dispenses 20 EUR
    And Alice's balance is 80 EUR

Withdrawal above the balance is refused
    [Documentation]    Rule: an account cannot be overdrawn at the ATM.
    [Tags]    rule:no-overdraft
    Given Alice has a balance of 10 EUR
    When Alice withdraws 20 EUR
    Then the withdrawal is refused with "Insufficient funds"
    And no cash is dispensed
    And Alice's balance is 10 EUR

Withdrawal above the cash in the ATM is refused
    [Documentation]    Rule: the ATM never promises more cash than it holds.
    [Tags]    rule:atm-cash
    Given Alice has a balance of 900 EUR
    When Alice withdraws 600 EUR
    Then the withdrawal is refused with "ATM out of cash"
    And Alice's balance is 900 EUR
