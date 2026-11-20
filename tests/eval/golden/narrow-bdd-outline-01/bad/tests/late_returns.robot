*** Settings ***
Resource            returning_steps.resource


*** Test Cases ***
Fine 0
    Return late    0    0
Fine 1
    Return late    1    0.50
Fine 7
    Return late    7    3.50
Fine 30
    Return late    30    15.00
