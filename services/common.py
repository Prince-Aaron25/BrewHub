from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import re
from database import transaction
from models.user import from_row
from repositories.queries import one


def text_value(value, label, maximum, required=True):
    value = str(value or "").strip()
    if (required and not value) or len(value) > maximum:
        raise ValueError(f"{label} is required and must be at most {maximum} characters." if required
                         else f"{label} must be at most {maximum} characters.")
    return value


def email_value(value):
    value = text_value(value, "Email", 100).lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise ValueError("Enter a valid email address.")
    return value


def amount(value, label="Amount", positive=False):
    try:
        n = Decimal(str(value))
        if not n.is_finite() or n < 0 or n > Decimal("99999999.99") or n != n.quantize(Decimal(".01")):
            raise ValueError()
        if positive and n <= 0:
            raise ValueError()
        return n.quantize(Decimal(".01"))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{label} must be {'positive' if positive else 'zero or positive'}, with at most 2 decimals.") from None


class Service:
    def __init__(self, user):
        self.user = user

    @contextmanager
    def tx(self, permission=None, write=False):
        with transaction(write=write) as cur:
            row = one(cur, "SELECT * FROM users WHERE user_id=%s", (self.user.user_id,))
            if not row or row["status"] != "active":
                raise ValueError("Your account is inactive. Please log out.")
            current = from_row(row)
            if permission and not current.can(permission):
                raise ValueError("This account does not have permission for that action.")
            self.user = current
            yield cur

