*** Settings ***
Documentation       As an account holder
...                 I want a daily limit on ATM withdrawals
...                 So that a stolen card cannot empty my account
Metadata            Feature    Daily withdrawal limit
Resource            cash_withdrawal_steps.resource
Test Setup          Given the daily withdrawal limit is 300 EUR
Test Tags           feature:daily-withdrawal-limit    rule:within-daily-limit


*** Test Cases ***
Withdrawal within the daily limit is dispensed
    [Documentation]    Rule: withdrawals up to the daily limit are dispensed.
    Given Bob has a balance of 1000 EUR
    And Bob has already withdrawn 200 EUR today
    When Bob withdraws 100 EUR
    Then the ATM dispenses 100 EUR

Withdrawal above the daily limit is refused
    [Documentation]    Rule: a withdrawal that would exceed the daily limit is refused.
    Given Bob has a balance of 1000 EUR
    And Bob has already withdrawn 250 EUR today
    When Bob withdraws 100 EUR
    Then the withdrawal is refused with "Daily limit exceeded"
    And Bob's balance is 750 EUR
