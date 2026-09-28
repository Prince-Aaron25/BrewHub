from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Product:
    product_id: int
    product_name: str
    price: Decimal
    availability: bool = True

