*** Settings ***
Documentation       As an account holder
...                 I want to withdraw cash from an ATM
...                 So that I can get money when the bank is closed
Metadata            Feature    Cash withdrawal
Library             CashWithdrawalWorld
Test Setup          Given the ATM holds 500 EUR
Test Tags           feature:cash-withdrawal


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
    And Alice's balance is 10 EUR
