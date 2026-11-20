"""Lending service of the city library (in-memory backend).

Rules:
- A member borrows a book if a copy is available, the member is not blocked,
  has no unpaid fines and is below the loan limit (standard: 3, premium: 10).
- Loans are due 21 days after the lending day.
- Returning late costs 0.50 EUR per day; the fine is added to the member's account.
- A member may reserve a book that has no copy available; reservations queue in order.
- A reserved returned copy is held for the first member in the queue.
"""

from datetime import date, timedelta
from decimal import Decimal

from robot.api.deco import keyword, library

LOAN_LIMITS = {"standard": 3, "premium": 10}
LOAN_DAYS = 21
FINE_PER_DAY = Decimal("0.50")


@library(scope="TEST")
class LibraryService:
    """Fake library backend. A fresh instance is created for every test."""

    def __init__(self) -> None:
        self._today = date(2026, 11, 12)
        self._copies: dict[str, int] = {}
        self._members: dict[str, dict] = {}
        self._loans: dict[str, dict[str, date]] = {}
        self._reservations: dict[str, list[str]] = {}
        self._held_for: dict[str, list[str]] = {}
        self._last_receipt = ""

    @keyword
    def set_today(self, day: date) -> None:
        """Sets the library's current date (ISO format, e.g. 2026-11-12)."""
        self._today = day

    @keyword
    def add_book(self, title: str, copies: int = 1) -> None:
        """Adds ``copies`` copies of ``title`` to the shelf."""
        self._copies[title] = self._copies.get(title, 0) + copies

    @keyword
    def register_member(self, name: str, membership: str = "standard") -> None:
        """Registers a member with a ``standard`` or ``premium`` membership."""
        if membership not in LOAN_LIMITS:
            raise ValueError(f"Unknown membership '{membership}'")
        self._members[name] = {"membership": membership, "fines": Decimal("0"), "blocked": False}
        self._loans[name] = {}

    @keyword
    def block_member(self, name: str) -> None:
        """Blocks a member; blocked members cannot borrow."""
        self._members[name]["blocked"] = True

    @keyword
    def add_fine(self, name: str, amount: Decimal) -> None:
        """Adds an unpaid fine of ``amount`` EUR to a member's account."""
        self._members[name]["fines"] += Decimal(amount)

    @keyword
    def borrow(self, name: str, title: str) -> dict:
        """Requests a loan. Returns ``{status, reason, due_date}``."""
        member = self._members[name]
        if member["blocked"]:
            return self._refused("Member is blocked")
        if member["fines"] > 0:
            return self._refused("Unpaid fines")
        if len(self._loans[name]) >= LOAN_LIMITS[member["membership"]]:
            return self._refused("Loan limit reached")
        held = self._held_for.get(title, [])
        if held and held[0] != name:
            return self._refused("Copy is reserved for another member")
        if held:
            held.pop(0)
        elif self._copies.get(title, 0) <= 0:
            return self._refused("No copy available")
        else:
            self._copies[title] -= 1
        due = self._today + timedelta(days=LOAN_DAYS)
        self._loans[name][title] = due
        self._last_receipt = f"Title: {title}\nDue: {due.isoformat()}"
        return {"status": "lent", "reason": None, "due_date": due}

    @keyword
    def return_book(self, name: str, title: str) -> Decimal:
        """Returns a loan on today's date. Returns the fine charged (EUR)."""
        due = self._loans[name].pop(title)
        days_late = max((self._today - due).days, 0)
        fine = FINE_PER_DAY * days_late
        self._members[name]["fines"] += fine
        queue = self._reservations.get(title, [])
        if queue:
            self._held_for.setdefault(title, []).append(queue.pop(0))
        else:
            self._copies[title] = self._copies.get(title, 0) + 1
        return fine

    @keyword
    def reserve(self, name: str, title: str) -> int:
        """Reserves ``title``; returns the member's position in the queue (1-based)."""
        if self._copies.get(title, 0) > 0:
            raise ValueError(f"'{title}' is available; reserve only unavailable books")
        queue = self._reservations.setdefault(title, [])
        queue.append(name)
        return len(queue)

    @keyword
    def get_loans(self, name: str) -> list[str]:
        """Returns the titles ``name`` currently has on loan, sorted."""
        return sorted(self._loans[name])

    @keyword
    def get_fines(self, name: str) -> Decimal:
        """Returns the unpaid fines of ``name`` in EUR."""
        return self._members[name]["fines"]

    @keyword
    def get_available_copies(self, title: str) -> int:
        """Returns how many copies of ``title`` are on the shelf."""
        return self._copies.get(title, 0)

    @keyword
    def get_last_receipt(self) -> str:
        """Returns the text of the last loan receipt."""
        return self._last_receipt

    @staticmethod
    def _refused(reason: str) -> dict:
        return {"status": "refused", "reason": reason, "due_date": None}
