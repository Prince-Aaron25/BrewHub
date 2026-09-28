# Final acceptance checks on your Windows computer

Use temporary menu items/customer accounts. Check stock before/after each action.
Keep screenshots of results for your defense. Fill in Actual and Pass/Fail yourself.

| ID | Steps | Expected | Actual | Pass/Fail |
|---|---|---|---|---|
| A01 | Register, then log in as customer | Customer dashboard opens | | |
| A02 | Register same email again | Rejected; no duplicate account | | |
| A03 | Enter wrong password | Login rejected | | |
| A04 | Log in as admin | Admin dashboard opens | | |
| A05 | Deactivate customer; try existing session/new login | Customer actions/login denied | | |
| C01 | Add category, product, image | Product appears in customer menu | | |
| C02 | Change product to unavailable | Hidden from new menu browsing | | |
| C03 | Add item then make it unavailable before checkout | Checkout rejects it; item can be removed | | |
| I01 | Add ingredient and Stock In 1000 | Quantity is 1000; history shows movement | | |
| I02 | Set reorder level equal to quantity | Low-stock indicator is true | | |
| I03 | Stock Out more than available | Rejected; quantity unchanged | | |
| O01 | Add 2 products priced PHP 120 each | Cart total PHP 240 | | |
| O02 | Submit cart | One Pending order; cart cleared | | |
| O03 | Refresh My orders | Saved order still visible | | |
| O04 | Confirm recipe using 200 ml each | Two products deduct 400 ml once | | |
| O05 | Confirm same order again | Rejected; no second deduction | | |
| O06 | Confirm order with insufficient stock | All stock/order state unchanged | | |
| O07 | Customer cancels Pending order | Cancelled; no stock movement | | |
| O08 | Customer cancels Confirmed order | Rejected | | |
| O09 | Admin cancels Confirmed order | Original stock deduction restored once | | |
| O10 | Admin cancels Preparing order | Ingredients remain consumed | | |
| P01 | Cash PHP 300 for order PHP 240 | Change PHP 60; applied amount PHP 240 | | |
| P02 | Record same payment again | Rejected | | |
| P03 | GCash without reference or wrong amount | Rejected | | |
| P04 | Verified GCash, correct total, unique reference | Paid | | |
| P05 | Use same GCash reference on another order | Rejected | | |
| P06 | Advance unpaid Ready order | Completion rejected | | |
| P07 | Refund after manually returning full payment | Refunded once; no stock change | | |
| R01 | Complete fully paid order; show today's sales | Included exactly once | | |
| R02 | Refund completed order | Excluded from operational sales totals | | |
| R03 | Export receipt, sales PDF/CSV, inventory PDF | Files open with correct numbers | | |
| U01 | Edit profile, log out/in | Details persist | | |
| U02 | Change password | New password works, old one fails | | |
| D01 | Restart application | Accounts, stock and orders persist | | |
| D02 | Stop MySQL and perform an action | Helpful error; app stays open | | |
| D03 | Rerun setup after backing up | Existing records preserved | | |

Use the PDF receipt and database queries to compare exact totals. Passing tests
here confirms behavior on your own Windows/Python/MySQL installation.

