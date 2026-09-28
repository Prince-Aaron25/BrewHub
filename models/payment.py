from abc import ABC, abstractmethod
from decimal import Decimal


class Payment(ABC):
    @abstractmethod
    def validate(self, total, tendered, reference):
        pass


class CashPayment(Payment):
    def validate(self, total, tendered, reference=""):
        if tendered < total:
            raise ValueError("Cash received is less than the order total.")
        return tendered - total


class GCashPayment(Payment):
    def validate(self, total, tendered, reference):
        if not reference.strip():
            raise ValueError("Enter the verified GCash reference number.")
        if tendered != total:
            raise ValueError("Verified GCash amount must equal the order total.")
        return Decimal("0.00")

