*** Settings ***
Documentation       As an account holder
...                 I want to withdraw cash from an ATM
...                 So that I can get money when the bank is closed
Metadata            Feature    Cash withdrawal
Resource            cash_withdrawal_steps.resource
Test Setup          Given the ATM holds 500 EUR
Test Tags           feature:cash-withdrawal
