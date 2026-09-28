# BrewHub UML and OOP guide

These diagrams describe the actual Python classes delivered in this package.
Paste a `.mmd` file's contents into mermaid.live. Database columns are documented
in `sql/schema.sql` and `setup_db.py`; UML shows Python behavior, not just tables.

## Account types: abstraction, inheritance and polymorphism

```mermaid
classDiagram
direction TB
class User {
    <<abstract>>
    +int user_id
    +str full_name
    +str email
    +str phone
    +get_permissions()*
    +can(permission) bool
}
class Customer {
    +get_permissions() frozenset
}
class Admin {
    +get_permissions() frozenset
}
class AuthService {
    +register(name, email, phone, password)
    +login(email, password) User
}
class Service {
    +User user
    +tx(permission, write)
}
User <|-- Customer
User <|-- Admin
AuthService ..> User : returns
Service --> User : checks permissions
```

`User` cannot be created directly. `Customer` and `Admin` implement the same
`get_permissions()` method differently. `can()` uses that polymorphic method.
The services reload the user's current account from the database before operations.

## Ordering: composition and encapsulation

```mermaid
classDiagram
direction TB
class Product {
    +int product_id
    +str product_name
    +Decimal price
    +bool availability
}
class Order {
    -list _items
    +items tuple
    +add_item(product, quantity)
    +calculate_total() Decimal
}
class OrderItem {
    +int product_id
    +str product_name
    +int quantity
    +Decimal unit_price
    +subtotal() Decimal
}
class OrderService {
    +quote(cart) Order
    +place_order(cart, request_token, expected_total) int
    +list_orders(status)
    +details(order_id)
    +confirm(order_id)
    +advance(order_id)
    +cancel(order_id, reason)
}
Order "1" *-- "0..*" OrderItem : owns
Order ..> Product : copies price and name
OrderService ..> Order : builds validated order
```

`Order.add_item()` constructs each order line. The public `items` property returns
a tuple so callers cannot append to the internal list. Each `OrderItem` is a frozen
dataclass. New order lines save their original name and price to the database.
The draft can be empty, but `place_order()` rejects an empty cart.

The composition relationship describes domain ownership. Python garbage collection
does not promise an object is physically destroyed immediately when another object
is deleted. Persistent order lines stay linked to their order; the app preserves
order history instead of deleting completed orders.

## Payments: a second polymorphism example

```mermaid
classDiagram
direction TB
class Payment {
    <<abstract>>
    +validate(total, tendered, reference)*
}
class CashPayment {
    +validate(total, tendered, reference) Decimal
}
class GCashPayment {
    +validate(total, tendered, reference) Decimal
}
class PaymentService {
    +record(order_id, method, tendered, reference) Decimal
    +refund(order_id, reason) Decimal
}
Payment <|-- CashPayment
Payment <|-- GCashPayment
PaymentService ..> Payment : validates through same method
```

Cash allows overpayment and returns change. GCash requires the exact amount and
a reference. Both use `validate()`. `PaymentService` adds database checks, including
admin permission, duplicate payments and reused references. This is manual payment
recording, not payment-gateway integration.

## Inventory

```mermaid
classDiagram
direction TB
class Ingredient {
    +int ingredient_id
    +str ingredient_name
    +Decimal quantity
    +str unit
    +Decimal reorder_level
    +is_low() bool
}
class InventoryService {
    +ingredients(low_only)
    +save_ingredient(name, unit, reorder, ingredient_id)
    +adjust(ingredient_id, kind, quantity, reason)
    +history()
    +delete_ingredient(ingredient_id)
}
class CatalogService {
    +categories()
    +save_category(name, category_id)
    +products(search, category_id, include_unavailable)
    +save_product(name, category_id, description, price, image_path, available, product_id)
    +recipe(product_id)
    +save_recipe_line(product_id, ingredient_id, quantity)
    +remove_recipe_line(product_id, ingredient_id)
}
class OrderService {
    +confirm(order_id)
    +cancel(order_id, reason)
}
InventoryService ..> Ingredient : calculates low stock
CatalogService ..> Ingredient : recipe data
OrderService ..> Ingredient : consumes stock
```

All service classes except `AuthService` inherit the common `Service` class.
`ReportService` exposes `summary`, `sales`, `export_sales`, `export_inventory` and
`receipt`. `ProfileService` exposes profile updates, password changes and customer
account management. Their full signatures are in the matching Python files.

## Symbol guide

- `+`: public attribute/method.
- `-`: internal/nonpublic in the design; Python uses conventions/properties.
- Triangle: inheritance.
- Filled diamond: composition/ownership.
- Dotted arrow: uses/depends on another class.
- `0..*`: zero or more in a draft; order submission requires one or more.

