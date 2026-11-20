*** Settings ***
Documentation       Technical smoke check: the service library loads and lends a book.
Library             LibraryService


*** Test Cases ***
Service lends an available copy
    Register Member    Smoke Reader
    Add Book    Smoke Test Title    1
    ${loan}    Borrow    Smoke Reader    Smoke Test Title
    Should Be Equal    ${loan}[status]    lent
    Should Be Equal As Strings    ${loan}[due_date]    2026-12-03
