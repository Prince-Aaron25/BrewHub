# Verification results

Prepared on 2026-09-27.

## Automated results

- 34 tests passed: 11 model/validation tests, 22 MySQL service integration tests,
  and 1 populated legacy-schema migration test.
- Real database: MySQL Community Server 8.0.46, using InnoDB.
- GUI smoke check passed after the final UI corrections: real CustomTkinter
  windows, login/register screens, every customer/admin tab, cart submission,
  product edit dialog, order confirmation/completion and report exports.
- PDF receipts, sales and inventory reports were generated and visually inspected.
- Python source compiled successfully; the archive is checked before delivery.

## What the tests cover

- Abstract classes, account permissions, exact Decimal calculations and composition.
- Password hashing, duplicate registration, incorrect passwords and changed passwords.
- Account deactivation affecting an existing session; restricted customer/admin actions.
- Order ownership/privacy, request-token deduplication and original price/name snapshots.
- Insufficient stock, missing recipes, duplicate confirmations and transaction rollback
  after an injected failure partway through confirmation.
- Two concurrent confirmations of one order and two orders competing for one serving.
- Cancellation before/after preparation; restoring the original snapshot after recipe edits.
- Cash change, insufficient cash, duplicate payments, GCash reference reuse and full refunds.
- Preventing unpaid completion; counting completed paid orders and excluding refunds.
- Date validation, PDF receipts, inventory PDF and CSV export.
- Repeated setup on populated databases, preserving account hashes and existing order data.
- Retaining historical products and ingredients.

## Environment and limits

Tests ran on Linux with Python 3.12.14, CustomTkinter 6.0.0,
mysql-connector-python 26.7.0, Pillow 12.3.0, ReportLab 4.4.9 and argon2-cffi 25.1.0.
The test database was isolated. No connection was made to your computer or your
actual brewhub_db. Your original code/schema were reviewed from screenshots.

Your Windows/Python 3.14 installation, actual existing data, printer behavior,
network setup and individual pictures still need the included manual acceptance
checks. These results establish the tested workflows; they are not a promise of
zero bugs in every environment. MySQL must be running separately.

Cash/GCash and refund checks verify record handling only; no money is transferred
by this application. Images/products/ingredients remain for you to add.
