"""Step definitions and scenario state ("World") for the cash withdrawal domain.

Opt-in alternative to a step ``.resource``: use it when the project already
keeps steps in Python, or when steps need real logic. ``scope="TEST"`` gives
every test a fresh World, so no state leaks between scenarios.

Each ``@keyword`` name is one domain sentence. The BDD prefixes (Given, When,
Then, And, But) are stripped by Robot Framework and are never part of a name.
"""

from __future__ import annotations

from robot.api.deco import keyword, library

from AtmService import AtmService


@library(scope="TEST")
class CashWithdrawalWorld:
    """Cash withdrawal steps. State lives on the instance, not in RF variables."""

    def __init__(self) -> None:
        self.atm = AtmService()  # technical layer; Browser/Requests in a real project
        self.last_withdrawal: dict | None = None

    # --- Given -----------------------------------------------------------

    @keyword("The ATM holds ${cash} EUR")
    def the_atm_holds(self, cash: int) -> None:
        """Loads the ATM with ``cash`` euros."""
        self.atm.load_atm(cash)

    @keyword("${holder} has a balance of ${amount} EUR")
    def has_a_balance_of(self, holder: str, amount: int) -> None:
        """Opens an account for ``holder`` with ``amount`` euros."""
        self.atm.open_account(holder, amount)

    # --- When ------------------------------------------------------------

    @keyword("${holder} withdraws ${amount} EUR")
    def withdraws(self, holder: str, amount: int) -> None:
        """``holder`` requests ``amount`` euros at the ATM."""
        self.last_withdrawal = self.atm.request_withdrawal(holder, amount)

    # --- Then ------------------------------------------------------------

    @keyword("The ATM dispenses ${amount} EUR")
    def the_atm_dispenses(self, amount: int) -> None:
        """The last withdrawal was dispensed with exactly ``amount`` euros."""
        result = self._last()
        if result["status"] != "dispensed" or result["dispensed"] != amount:
            raise AssertionError(f"Expected {amount} EUR to be dispensed, but the ATM reported {result}")

    @keyword('The withdrawal is refused with "${reason}"')
    def the_withdrawal_is_refused_with(self, reason: str) -> None:
        """The last withdrawal was refused, and the ATM showed ``reason``."""
        result = self._last()
        if result["status"] != "refused" or result["reason"] != reason:
            raise AssertionError(f'Expected a refusal with "{reason}", but the ATM reported {result}')

    @keyword("${holder}'s balance is ${amount} EUR")
    def balance_is(self, holder: str, amount: int) -> None:
        """The account of ``holder`` holds exactly ``amount`` euros."""
        balance = self.atm.get_balance(holder)
        if balance != amount:
            raise AssertionError(f"{holder}'s balance is {balance} EUR, expected {amount} EUR")

    def _last(self) -> dict:
        if self.last_withdrawal is None:
            raise AssertionError("No withdrawal was made in this scenario")
        return self.last_withdrawal
