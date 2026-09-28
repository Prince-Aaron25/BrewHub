"""Opt-in real MySQL tests. Never point these at brewhub_db.
See README for the environment variables. Tests delete only their generated rows.
"""
import os
import unittest
from uuid import uuid4
from decimal import Decimal
from datetime import date
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from config import DB_CONFIG
from database import transaction
from repositories.queries import one
from setup_db import migrate, create_admin
from services.auth_service import AuthService
from services.catalog_service import CatalogService
from services.inventory_service import InventoryService
from services.order_service import OrderService
from services.payment_service import PaymentService
from services.profile_service import ProfileService
from services.report_service import ReportService

ENABLED = os.getenv("BREWHUB_RUN_DB_TESTS") == "1"


@unittest.skipUnless(ENABLED,"Set BREWHUB_RUN_DB_TESTS=1 and use brewhub_test_db for integration tests")
class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if DB_CONFIG["database"] != "brewhub_test_db":
            raise RuntimeError("Integration tests require the separate database brewhub_test_db.")
        migrate()

    def setUp(self):
        self.tag = uuid4().hex[:12]
        self.emails = [f"{self.tag}{n}@example.test" for n in range(3)]
        create_admin("Test admin",self.emails[0],"TestPass123")
        auth = AuthService()
        auth.register("Test customer",self.emails[1],"","TestPass123")
        auth.register("Other customer",self.emails[2],"","TestPass123")
        self.admin,self.customer,self.other = [auth.login(email,"TestPass123") for email in self.emails]
        self.catalog = CatalogService(self.admin)
        self.inv = InventoryService(self.admin)
        self.orders = OrderService(self.admin)
        self.checkout = OrderService(self.customer)
        self.pay = PaymentService(self.admin)
        self.cat = self.catalog.save_category("Test "+self.tag)
        self.product = self.catalog.save_product("Latte "+self.tag,self.cat,"Test",Decimal("120"),"",True)
        self.ingredient = self.inv.save_ingredient("Milk "+self.tag,"ml",100)
        self.inv.adjust(self.ingredient,"Stock In",1000,"Opening stock")
        self.catalog.save_recipe_line(self.product,self.ingredient,200)

    def tearDown(self):
        # Only rows owned by these freshly generated test accounts/products.
        with transaction(write=True) as cur:
            ids = (self.admin.user_id,self.customer.user_id,self.other.user_id)
            cur.execute("SELECT order_id FROM orders WHERE user_id IN (%s,%s,%s)",ids)
            for row in cur.fetchall():
                for table in ("payments","order_stock","order_items"):
                    cur.execute(f"DELETE FROM {table} WHERE order_id=%s",(row["order_id"],))
            cur.execute("DELETE FROM orders WHERE user_id IN (%s,%s,%s)",ids)
            cur.execute("DELETE FROM product_ingredients WHERE product_id=%s",(self.product,))
            cur.execute("DELETE FROM products WHERE product_id=%s",(self.product,))
            cur.execute("DELETE FROM categories WHERE category_id=%s",(self.cat,))
            cur.execute("DELETE FROM inventory_transactions WHERE ingredient_id=%s",(self.ingredient,))
            cur.execute("DELETE FROM ingredients WHERE ingredient_id=%s",(self.ingredient,))
            cur.execute("DELETE FROM users WHERE user_id IN (%s,%s,%s)",ids)

    def place(self, qty=1, token=None):
        return self.checkout.place_order({self.product:qty},token or str(uuid4()),Decimal("120")*qty)

    def stock(self):
        return next(r["quantity"] for r in self.inv.ingredients() if r["ingredient_id"]==self.ingredient)

    def test_full_cash_workflow_and_report(self):
        oid = self.place(2)
        self.orders.confirm(oid)
        self.assertEqual(self.stock(),Decimal("600"))
        self.assertEqual(self.pay.record(oid,"Cash",300),Decimal("60"))
        self.assertEqual(self.orders.advance(oid),"Preparing")
        self.assertEqual(self.orders.advance(oid),"Ready")
        self.assertEqual(self.orders.advance(oid),"Completed")
        groups,rows = ReportService(self.admin).sales(date.today(),date.today())
        self.assertIn(oid,[r["order_id"] for r in rows])
        receipt = ReportService(self.customer).receipt(oid)
        self.assertTrue(receipt.read_bytes().startswith(b"%PDF"))
        receipt.unlink()

    def test_duplicate_submission_and_confirmation(self):
        token = str(uuid4())
        oid = self.place(1,token)
        self.assertEqual(oid,self.place(1,token))
        self.orders.confirm(oid)
        with self.assertRaises(ValueError): self.orders.confirm(oid)
        self.assertEqual(self.stock(),800)

    def test_concurrent_confirmation_deducts_once(self):
        oid = self.place()
        def attempt():
            try: OrderService(self.admin).confirm(oid); return True
            except ValueError: return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _:attempt(),range(2)))
        self.assertEqual(sum(results),1)
        self.assertEqual(self.stock(),800)

    def test_two_orders_compete_for_stock(self):
        self.inv.adjust(self.ingredient,"Adjustment",200,"One serving left")
        ids = [self.place(),self.place()]
        def attempt(oid):
            try: OrderService(self.admin).confirm(oid); return True
            except ValueError: return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt,ids))
        self.assertEqual(sum(results),1)
        self.assertEqual(self.stock(),0)

    def test_insufficient_stock_leaves_pending(self):
        oid = self.place(6)
        with self.assertRaises(ValueError): self.orders.confirm(oid)
        self.assertEqual(self.stock(),1000)
        self.assertEqual(self.checkout.details(oid)[0]["status"],"Pending")

    def test_cancel_uses_original_stock_snapshot(self):
        oid = self.place()
        self.orders.confirm(oid)
        self.catalog.save_recipe_line(self.product,self.ingredient,350)
        self.orders.cancel(oid,"Customer changed mind")
        self.assertEqual(self.stock(),1000)
        with self.assertRaises(ValueError): self.orders.cancel(oid,"Again")

    def test_prepared_cancel_does_not_restore(self):
        oid = self.place()
        self.orders.confirm(oid)
        self.orders.advance(oid)
        self.orders.cancel(oid,"Spoiled drink")
        self.assertEqual(self.stock(),800)

    def test_customer_can_only_cancel_own_pending(self):
        oid = self.place()
        with self.assertRaises(ValueError): OrderService(self.other).cancel(oid,"Not mine")
        self.orders.confirm(oid)
        with self.assertRaises(ValueError): self.checkout.cancel(oid,"Too late")
        second = self.place()
        self.checkout.cancel(second,"Changed mind")
        self.assertEqual(self.checkout.details(second)[0]["status"],"Cancelled")

    def test_payment_duplicate_underpayment_and_refund(self):
        oid = self.place()
        self.orders.confirm(oid)
        with self.assertRaises(ValueError): self.pay.record(oid,"Cash",100)
        self.pay.record(oid,"GCash",120,"REF-"+self.tag)
        with self.assertRaises(ValueError): self.pay.record(oid,"Cash",120)
        self.orders.cancel(oid,"Cancelled")
        self.assertEqual(self.pay.refund(oid,"Returned manually"),120)
        with self.assertRaises(ValueError): self.pay.refund(oid,"Again")
        self.assertEqual(self.checkout.details(oid)[2]["payment_status"],"Refunded")

    def test_no_completion_without_payment(self):
        oid = self.place()
        self.orders.confirm(oid)
        self.orders.advance(oid)
        self.orders.advance(oid)
        with self.assertRaises(ValueError): self.orders.advance(oid)

    def test_price_snapshot_and_requote(self):
        oid = self.place()
        self.catalog.save_product("Renamed "+self.tag,self.cat,"",150,"",True,self.product)
        items = self.checkout.details(oid)[1]
        self.assertEqual(items[0]["unit_price"],120)
        self.assertEqual(items[0]["product_name"],"Latte "+self.tag)
        with self.assertRaises(ValueError): self.place()

    def test_permissions_and_inactive_session(self):
        with self.assertRaises(ValueError): CatalogService(self.customer).save_category("Forbidden")
        ProfileService(self.admin).set_status(self.customer.user_id,"inactive")
        with self.assertRaises(ValueError): self.place()
        with self.assertRaises(ValueError): AuthService().login(self.emails[1],"TestPass123")

    def test_profile_and_password_change(self):
        profile = ProfileService(self.customer)
        profile.update("Updated",self.emails[1],"09123456789")
        profile.change_password("TestPass123","Different123")
        self.assertEqual(AuthService().login(self.emails[1],"Different123").full_name,"Updated")
        with self.assertRaises(ValueError): AuthService().login(self.emails[1],"TestPass123")

    def test_migration_rerun_preserves_rows(self):
        oid = self.place()
        before = self.checkout.details(oid)
        migrate()
        self.assertEqual(before,self.checkout.details(oid))

    def test_missing_recipe_and_stock_validation(self):
        self.catalog.remove_recipe_line(self.product,self.ingredient)
        oid = self.place()
        with self.assertRaises(ValueError): self.orders.confirm(oid)
        with self.assertRaises(ValueError): self.inv.adjust(self.ingredient,"Stock Out",1001,"Too much")
        self.assertEqual(self.stock(),1000)

    def test_gcash_reference_reuse_rejected(self):
        ids = [self.place(),self.place()]
        for oid in ids: self.orders.confirm(oid)
        self.pay.record(ids[0],"GCash",120,"REF-"+self.tag)
        with self.assertRaises(ValueError): self.pay.record(ids[1],"GCash",120,"REF-"+self.tag)

    def test_failure_mid_confirmation_rolls_back_every_change(self):
        oid = self.place()
        with patch("services.order_service.record_stock",side_effect=ValueError("Simulated failure")):
            with self.assertRaises(ValueError): self.orders.confirm(oid)
        self.assertEqual(self.stock(),1000)
        self.assertEqual(self.checkout.details(oid)[0]["status"],"Pending")
        with transaction() as cur:
            self.assertEqual(one(cur,"SELECT COUNT(*) n FROM order_stock WHERE order_id=%s",(oid,))["n"],0)

    def test_duplicate_email_and_wrong_password(self):
        with self.assertRaises(ValueError): AuthService().register("Duplicate",self.emails[1],"","TestPass123")
        with self.assertRaises(ValueError): AuthService().login(self.emails[1],"WrongPassword")

    def test_history_prevents_deletion(self):
        oid = self.place()
        result = self.catalog.delete_product(self.product)
        self.assertIn("unavailable",result)
        self.assertEqual(self.checkout.details(oid)[1][0]["product_id"],self.product)
        with self.assertRaises(ValueError): self.inv.delete_ingredient(self.ingredient)

    def test_customer_order_history_is_private(self):
        oid = self.place()
        self.assertNotIn(oid,[r["order_id"] for r in OrderService(self.other).list_orders()])
        with self.assertRaises(ValueError): OrderService(self.other).details(oid)
        with self.assertRaises(ValueError): ReportService(self.customer).sales(date.today(),date.today())

    def test_full_refund_excluded_from_sales(self):
        oid = self.place()
        self.orders.confirm(oid)
        self.pay.record(oid,"Cash",120)
        for _ in range(3): self.orders.advance(oid)
        self.pay.refund(oid,"Quality issue; money returned")
        _,rows = ReportService(self.admin).sales(date.today(),date.today())
        self.assertNotIn(oid,[r["order_id"] for r in rows])

    def test_report_export_and_invalid_dates(self):
        report = ReportService(self.admin)
        with self.assertRaises(ValueError): report.sales("invalid","2026-09-27")
        with self.assertRaises(ValueError): report.sales("2026-09-27","2026-09-01")
        path = report.export_inventory()
        self.assertTrue(path.read_bytes().startswith(b"%PDF"));path.unlink()
        path = report.export_sales(date.today(),date.today(),"Monthly","csv")
        self.assertIn("TOTAL",path.read_text(encoding="utf-8-sig"));path.unlink()


if __name__ == "__main__":
    unittest.main()
