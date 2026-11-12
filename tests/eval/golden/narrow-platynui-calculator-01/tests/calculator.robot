*** Settings ***
Library    PlatynUI.BareMetal


*** Variables ***
${CALCULATOR}    //control:Window[@Name='Calculator' or @Name='Rechner']
${RESULT}        //control:Text[@Id='CalculatorResults']


*** Test Cases ***
One Plus Two Is Three
    Activate Window    ${CALCULATOR}
    Pointer Click    ${CALCULATOR}//control:Button[@Id='num1Button']
    Pointer Click    ${CALCULATOR}//control:Button[@Id='plusButton']
    Pointer Click    ${CALCULATOR}//control:Button[@Id='num2Button']
    Pointer Click    ${CALCULATOR}//control:Button[@Id='equalButton']
    ${shown}=    Get Attribute    ${RESULT}    Name
    Should Contain    ${shown}    3
