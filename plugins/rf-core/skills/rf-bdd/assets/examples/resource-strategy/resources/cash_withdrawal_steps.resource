*** Settings ***
Documentation       Step definitions for the cash withdrawal domain.
...
...                 One keyword is one domain sentence. Technical actions live in
...                 ``AtmService``; test cases only call the sentences below.
Library             AtmService


*** Variables ***
# Scenario state shared between steps. Declared here so static analysis
# knows it; steps assign it with ``VAR ... scope=TEST``.
${LAST_WITHDRAWAL}      ${None}


*** Keywords ***
The ATM holds ${cash: int} EUR
    [Documentation]    Loads the ATM with ``cash`` euros.
    Load ATM    ${cash}

The daily withdrawal limit is ${limit: int} EUR
    [Documentation]    Sets the maximum amount an account may withdraw per day.
    Set Daily Limit    ${limit}

${holder} has a balance of ${amount: int} EUR
    [Documentation]    Opens an account for ``holder`` with ``amount`` euros.
    Open Account    ${holder}    ${amount}

${holder} has already withdrawn ${amount: int} EUR today
    [Documentation]    Records an earlier successful withdrawal on the same day.
    ${result}    Request Withdrawal    ${holder}    ${amount}
    Should Be Equal    ${result}[status]    dispensed
    ...    msg=Precondition failed: the earlier withdrawal of ${amount} EUR was refused

${holder} withdraws ${amount: int} EUR
    [Documentation]    ``holder`` requests ``amount`` euros at the ATM.
    ${result}    Request Withdrawal    ${holder}    ${amount}
    VAR    ${LAST_WITHDRAWAL}    ${result}    scope=TEST

The ATM dispenses ${amount: int} EUR
    [Documentation]    The last withdrawal was dispensed with exactly ``amount`` euros.
    Should Be Equal    ${LAST_WITHDRAWAL}[status]    dispensed
    Should Be Equal    ${LAST_WITHDRAWAL}[dispensed]    ${amount}

The withdrawal is refused with "${reason}"
    [Documentation]    The last withdrawal was refused, and the ATM showed ``reason``.
    Should Be Equal    ${LAST_WITHDRAWAL}[status]    refused
    Should Be Equal    ${LAST_WITHDRAWAL}[reason]    ${reason}

No cash is dispensed
    [Documentation]    The last withdrawal dispensed nothing.
    Should Be Equal    ${LAST_WITHDRAWAL}[dispensed]    ${0}

${holder}'s balance is ${amount: int} EUR
    [Documentation]    The account of ``holder`` holds exactly ``amount`` euros.
    ${balance}    Get Balance    ${holder}
    Should Be Equal    ${balance}    ${amount}
