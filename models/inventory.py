from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Ingredient:
    ingredient_id: int
    ingredient_name: str
    quantity: Decimal
    unit: str
    reorder_level: Decimal

    def is_low(self):
        return self.quantity <= self.reorder_level

