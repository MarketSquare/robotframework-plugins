"""Stand-in for the system under test: a tiny in-memory ATM.

This is the *technical layer*. In a real project it is Browser, RequestsLibrary,
a database library or the project's own API client. Step keywords call it;
test cases never do. Keyword names here are classic RF Title Case actions.
"""

from __future__ import annotations

from robot.api.deco import keyword, library


@library(scope="TEST")
class AtmService:
    """Fake ATM and bank backend. A fresh instance is created for every test."""

    def __init__(self) -> None:
        self._cash = 10_000
        self._daily_limit = 1_000
        self._balances: dict[str, int] = {}
        self._withdrawn_today: dict[str, int] = {}
        self._last_receipt = ""

    @keyword
    def load_atm(self, cash: int) -> None:
        """Sets the amount of cash inside the ATM."""
        self._cash = cash

    @keyword
    def set_daily_limit(self, limit: int) -> None:
        """Sets the maximum amount one account may withdraw per day."""
        self._daily_limit = limit

    @keyword
    def open_account(self, holder: str, balance: int) -> None:
        """Opens an account for ``holder`` with the given ``balance``."""
        self._balances[holder] = balance
        self._withdrawn_today[holder] = 0

    @keyword
    def request_withdrawal(self, holder: str, amount: int) -> dict:
        """Requests a withdrawal and returns ``{status, dispensed, reason}``."""
        if amount <= 0 or amount % 10:
            return self._refused("Amount must be a multiple of 10 EUR")
        if amount > self._balances[holder]:
            return self._refused("Insufficient funds")
        if self._withdrawn_today[holder] + amount > self._daily_limit:
            return self._refused("Daily limit exceeded")
        if amount > self._cash:
            return self._refused("ATM out of cash")
        self._balances[holder] -= amount
        self._withdrawn_today[holder] += amount
        self._cash -= amount
        self._last_receipt = f"Withdrawal: {amount} EUR\nBalance: {self._balances[holder]} EUR"
        return {"status": "dispensed", "dispensed": amount, "reason": None}

    @keyword
    def get_last_receipt(self) -> str:
        """Returns the text printed on the receipt of the last dispensed withdrawal."""
        return self._last_receipt

    @keyword
    def get_balance(self, holder: str) -> int:
        """Returns the current balance of ``holder``."""
        return self._balances[holder]

    @staticmethod
    def _refused(reason: str) -> dict:
        return {"status": "refused", "dispensed": 0, "reason": reason}
