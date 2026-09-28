"""Order composes its own immutable OrderItem objects."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OrderItem:
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal

    def subtotal(self):
        return self.unit_price * self.quantity


class Order:
    def __init__(self):
        self._items = []

    @property
    def items(self):
        return tuple(self._items)  # callers cannot change the internal list

    def add_item(self, product, quantity):
        if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= 999:
            raise ValueError("Quantity must be a whole number from 1 to 999.")
        if not product.availability:
            raise ValueError("Product is unavailable.")
        if not product.price.is_finite() or product.price < 0:
            raise ValueError("Invalid product price.")
        self._items.append(OrderItem(product.product_id, product.product_name, quantity, product.price))

    def calculate_total(self):
        return sum((item.subtotal() for item in self._items), Decimal("0.00"))

