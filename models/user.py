"""Abstraction + inheritance + polymorphism used by the real application."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class User(ABC):
    user_id: int
    full_name: str
    email: str
    phone: str = ""

    @abstractmethod
    def get_permissions(self):
        """Each account type supplies its permissions."""

    def can(self, permission):
        return permission in self.get_permissions()


class Customer(User):
    def get_permissions(self):
        return frozenset({"menu", "order", "profile"})


class Admin(User):
    def get_permissions(self):
        return frozenset({"menu", "manage", "reports", "profile"})


def from_row(row):
    cls = Admin if row["role"] == "admin" else Customer
    return cls(row["user_id"], row["full_name"], row["email"], row.get("phone") or "")

