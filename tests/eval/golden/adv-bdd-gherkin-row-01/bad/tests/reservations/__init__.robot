*** Settings ***
Documentation       As a library member
...                 I want to reserve a book that is on loan
...                 So that I get it as soon as it is returned
Metadata            Feature    Reservations
Metadata            Ticket    LIB-214
Resource            reservation_steps.resource
Test Tags           feature:reservations
Test Setup          Given the only copy of "Dune" is on loan to Mia
