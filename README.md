# BrewHub - start here

This package completes the simple desktop app shown in your screenshots. It uses
CustomTkinter, Python and your MySQL database (`brewhub_db`, port `3307`).
The app starts without any products, images or ingredients. Add yours through
the admin screens. You do not need to edit Python to add menu data.

## 1. Keep your existing work

1. Close your old BrewHub app.
2. Make a copy of your old project folder.
3. In MySQL Workbench, use **Server > Data Export**, select **brewhub_db**, choose
   **Export to Self-Contained File**, and start the export. Keep the resulting SQL backup.
4. Extract this ZIP into a new folder, such as `C:\BrewHub_Complete`. Open the inner
   `BrewHub` folder containing `main.py` in VS Code.
5. Keep your existing MySQL server and data. The setup script adds missing tables,
   columns and an index; it does not drop tables, clear records or seed products.

Using the extracted folder avoids mixing your old standalone login window with
the new `LoginView` class. If you prefer your original folder, copy ALL files from
this package into it after backing it up, replacing matching Python files. Keep
your own assets. Do not keep an old `database/` package alongside `database.py`.

## 2. Install the Python packages

You already have Python, VS Code, MySQL Server and Workbench. You do not need to
reinstall them. In VS Code, open **Terminal > New Terminal** in this folder.
Run these commands one at a time (Windows PowerShell):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

This installs CustomTkinter, MySQL Connector, Pillow, ReportLab and argon2-cffi.
`unittest` is included with Python. There is no need for pandas, FastAPI, Aiven,
SQLAlchemy, a browser server or a GCash API for this version.

In VS Code, use **Python: Select Interpreter** and choose `.venv\Scripts\python.exe`.
If `py` does not work but `python` does, use `python -m venv .venv` for the first command.

## 3. Enter your own database settings

Copy `config_local.example.py` and name the copy `config_local.py`.
Edit the clearly marked values in that new file:

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "brewhub_db",
}
```

Use your MySQL password here. The package does not include the password from your
screenshot. This is a database login, separate from the app admin/customer accounts.
Do not post `config_local.py` or commit it to GitHub.

## 4. Prepare the database and create an admin

Make sure your Windows **MySQL80** service is running. Then run:

```powershell
.\.venv\Scripts\python.exe setup_db.py
```

When asked **Create a NEW admin account?**, type `y`. Enter a name, email and a
password with at least 8 characters. Password typing is hidden in the terminal;
that is normal. This admin email/password is what you use in the application.

If an admin already exists, answer `n`. To create another admin, rerun the script.
The script will never silently promote or overwrite an existing email address.

If you had accounts with plaintext or another unsupported password format, the
records are kept but login will not accept the old format. Reset a known account:

```powershell
.\.venv\Scripts\python.exe setup_db.py --reset-password your-email@example.com
```

The reset keeps the user's ID, role, status and order history. Customer passwords
can also be reset by an admin in **Users**.

Run setup with the old app closed. MySQL schema changes commit individually; if
setup reports an unexpected schema, stop and share that error instead of deleting
the database. It is safe to rerun after a corrected installation problem.

## 5. Start BrewHub

```powershell
.\.venv\Scripts\python.exe main.py
```

After setup, you can also double-click `start.bat`. Run only `main.py`; do not run
`views/login_view.py` directly. There is one application window and one main loop.

## 6. Add YOUR products, pictures and ingredients

Log in as admin. Follow this order:

1. **Products > Categories > Add**: create your categories.
2. **Inventory > Add ingredient**: enter the ingredient name, unit (g for solid ingredients, ml for liquids, and pcs for individually counted items), and low-stock threshold.
3. Select an ingredient and click **Change stock > Stock In**: enter your starting
   quantity and a reason such as `Opening stock`.
4. **Products > Add product**: choose a category, price and description; set Available
   to Yes. Leave Image path blank for now.
5. Select the product and use **Choose picture for selected product** when ready.
   A portable image copy is saved under `assets/images`.
6. **Recipes**: select a product, click **Add / update ingredient**, and enter the
   amount used for **ONE** product. Repeat for every ingredient.

Example ONLY (not automatically inserted): one latte could use 18 grams of beans,
200 ml of milk and 1 cup. Two lattes use twice those amounts.

For a prepacked item such as bottled water, create an ingredient called `Bottled
water stock`, use unit `piece`, add the number of bottles in stock, and set its
product recipe to 1 piece. Every confirmed product must have a recipe.

Use one unit per ingredient. If milk is stored in ml, enter 1000 for a 1-liter
delivery. Quantity fields match your existing schema: at most two decimal places.
Units cannot change after creation because doing so would change the meaning of
existing stock and recipes. Create another ingredient if a different unit is needed.

## 7. Test a complete order yourself

1. Log out and use **Create customer account**.
2. Log in as that customer.
3. In **Menu**, select a product, enter quantity, and add it to the cart.
4. Open **Cart**, check the prices, and submit.
5. Open **My orders** to see Pending. Customers can cancel only Pending orders.
6. Log in as admin and open **Orders & payments**.
7. Select the order and click **Confirm + deduct stock**. If stock is insufficient,
   nothing is deducted. Fix stock or the recipe, then try again.
8. Click **Next status** to change Confirmed to Preparing, then Ready.
9. Use **Record payment**. For Cash, enter money received; change is calculated.
   For GCash, manually verify the money in your GCash account and enter its exact
   amount and reference. Choose `Yes - received and verified` only after checking.
10. Click **Next status** to complete the paid order.
11. Use **PDF receipt**, then check **Reports** and **Inventory**.

Use Refresh or switch tabs to see changes made by another user. The program does
not silently reserve stock for pending carts or orders; stock is checked when the
admin confirms an order.

## 8. Exact business rules in this version

| Area | Rule |
|---|---|
| Order flow | Pending -> Confirmed -> Preparing -> Ready -> Completed |
| Stock deduction | Once, at confirmation; all ingredients succeed or none do |
| Customer cancellation | Own Pending orders only |
| Admin cancellation | Pending, Confirmed, Preparing or Ready |
| Confirmed cancellation | Restore the original deducted quantities before preparation |
| Preparing/Ready cancellation | Keep ingredients consumed; do not restore used ingredients |
| Payment | Full Cash or manually verified GCash; no partial payments |
| Cash | Store order amount applied, amount tendered and change separately |
| GCash | Exact order total and a reference not already used on another order |
| Refund | Admin records the full refund only after actually returning money |
| Refund stock | No automatic stock restoration by a refund |
| Completion | Full payment required |
| Sales | Fully paid, completed, non-refunded orders; grouped by completion date |
| Legacy sales dates | Order date is used when an old completion date is unavailable |
| Weekly reports | Monday is the start of the week; only the selected date range is counted |
| Product removal | Delete unused products; mark products with order history unavailable |
| Ingredient removal | Delete only ingredients unused by recipes and stock history |
| User removal | Deactivate customers, preserving their order history |
| Access | Services recheck the account's current role and active status |

The app records payments and refunds; it does not transfer money or verify GCash
automatically. Cancelled orders that are still Paid appear under **Refunds to return**
on the admin overview. A refunded completed order is excluded from sales for its
original date; this is an operational sales report, not a full accounting ledger.

All app writes use one database transaction lock for a single cafe. This prevents
competing confirmations and recipe edits from producing inconsistent stock.
Keep other tools from manually editing order/stock rows while the application runs.

## 9. Existing records and old active orders

The setup keeps your original nine tables. It adds:

- `orders`: deduction flag, duplicate-request token, completion time, cancellation reason.
- `order_items`: original product-name snapshot for new orders.
- `payments`: tendered amount, change, admin ID, refund details.
- `inventory_transactions`: order ID and responsible admin ID.
- `order_stock`: exact ingredients deducted for each newly confirmed order.
- `app_mutex`: a transaction coordination row.

Existing passwords and records are not rewritten. Existing completed/cancelled
orders stay readable. A legacy Pending order can normally be confirmed using its
current recipe if it has not already been deducted.

For an old Confirmed/Preparing/Ready order with unknown deduction history, the app
stops rather than guessing stock usage. Check the physical stock, then either ask
for help reconciling that order or close it through:

```powershell
.\.venv\Scripts\python.exe close_legacy_order.py
```

That tool requires admin login and a typed order-specific confirmation. It marks
only an eligible legacy order Cancelled, keeps its history, and does not change
stock or payments. Use Inventory > Adjustment to record a checked physical count,
and record a real refund separately if needed.

## 10. OOP and UML for your defense

See `docs/UML.md` and the matching `.mmd` files.

| Concept | Real code to demonstrate |
|---|---|
| Classes/objects | `Product`, `Ingredient`, `Order`, `OrderItem`, account classes |
| Inheritance | `Customer` / `Admin` inherit `User`; payment types inherit `Payment` |
| Abstraction | `User.get_permissions()` and `Payment.validate()` are abstract methods |
| Polymorphism | Same permission call for different users; same validation call for Cash/GCash |
| Composition | `Order.add_item()` constructs its `OrderItem` objects |
| Encapsulation | `Order._items` is internal; `items` returns an immutable tuple |
| Separation | Views call services; services coordinate validation and database transactions |
| Testing | Unit, real MySQL integration, populated-schema migration and GUI checks |

Python's single underscore is a convention for nonpublic attributes, not absolute
privacy. Database table relationships and Python class relationships are related
designs, but are not the same diagram.

## 11. Run the tests

The ordinary command runs model tests without connecting to your real database;
database tests are reported as skipped until you explicitly enable them.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

To run integration tests, use a separate PowerShell terminal and the required
separate test database name. Keep the server/username/password from config_local.py:

```powershell
$env:BREWHUB_DB_DATABASE = "brewhub_test_db"
$env:BREWHUB_RUN_DB_TESTS = "1"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m tests.gui_smoke
Remove-Item Env:BREWHUB_DB_DATABASE
Remove-Item Env:BREWHUB_RUN_DB_TESTS
```

The test account needs permission to create/delete its temporary migration-test
database. Tests create temporary accounts, menu items and orders, then clean up
their own records. Never rename the production database to the test name.
Do not run the GUI test at the same time as another copy of the test suite.

See `docs/TEST_RESULTS.md` for the checks run while preparing this package, and
`docs/MANUAL_TESTS.md` for your final acceptance checklist on Windows.

## 12. File guide and design changes later

| File/folder | Purpose |
|---|---|
| `main.py` | Application entry point |
| `app.py` | Main window, navigation, login session, cart |
| `config_local.py` | Your private database settings (you create this) |
| `database.py` | MySQL connection and transaction handling |
| `setup_db.py` | Additive database setup and local admin creation/recovery |
| `models/` | OOP domain classes |
| `services/` | Authentication, catalog, inventory, orders, payments, profiles, reports |
| `repositories/queries.py` | Parameterized query helpers |
| `views/` | Every customer/admin screen |
| `assets/images/` | Your pictures; optional |
| `reports/` | Generated PDF/CSV files |
| `tests/` | Tests |
| `docs/` | UML and testing documentation |

To redesign later, begin with the `DESIGN LATER` comment in `app.py`, then edit the
widgets in `views/`. Keep service calls in button callbacks so behavior remains
connected. No logo is required; copy your original logo into assets/images if you
want to add it later. The inactive Remember Me checkbox from the screenshot is
not included; users sign in each time.

## Troubleshooting

| Symptom | What to do |
|---|---|
| ModuleNotFoundError | Install requirements using the same `.venv` Python you run |
| Database error 2003 | Start MySQL80 and verify host/port 3307 |
| Database error 1045 | Correct your MySQL username/password in config_local.py |
| Unknown database/table/column | Run setup_db.py using the same configuration |
| Admin email already exists | Answer n, log in, or reset that existing email's password |
| Legacy password fails | Use setup_db.py --reset-password EMAIL |
| No products visible | Add products, set Available=Yes, refresh; check category/search filter |
| Cannot confirm an order | Add a recipe for every item and enough stock for every ingredient |
| Connection failed during submit | Refresh My orders first. Retrying the unchanged cart uses the same request token |
| Image missing | Choose the image again through Products; optional images never block ordering |
| Unexpected error | Read logs/app.log; send that error without your private config file |

This is a local desktop application for a trusted cafe workstation/class project.
The MySQL database remains a separate running service; copying the Python folder
alone does not copy the server or database. An EXE installer is not included.

Official references used for implementation:
- https://customtkinter.tomschimansky.com/documentation/widgets/tabview/
- https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlconnection-start-transaction.html
- https://argon2-cffi.readthedocs.io/en/stable/howto.html

