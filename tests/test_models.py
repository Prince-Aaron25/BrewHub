import unittest
from decimal import Decimal
from models.user import User, Customer, Admin
from models.order import Order
from models.product import Product
from models.inventory import Ingredient
from models.payment import CashPayment, GCashPayment
from services.common import amount, email_value
from services.auth_service import HASHER, verify


class ModelTests(unittest.TestCase):
    def test_abstract_user_cannot_be_instantiated(self):
        with self.assertRaises(TypeError): User(1,"Name","a@example.com")

    def test_polymorphic_permissions(self):
        users = [Customer(1,"Customer","c@example.com"),Admin(2,"Admin","a@example.com")]
        self.assertEqual([u.can("manage") for u in users],[False,True])

    def test_order_owns_items_and_exact_total(self):
        order = Order()
        order.add_item(Product(1,"Latte",Decimal("120.10")),2)
        order.add_item(Product(2,"Cookie",Decimal("35.00")),1)
        self.assertEqual(order.calculate_total(),Decimal("275.20"))
        self.assertIsInstance(order.items,tuple)
        self.assertEqual(order.items[0].subtotal(),Decimal("240.20"))

    def test_order_rejects_invalid_quantities(self):
        for value in (0,-1,1.5,True,1000):
            with self.subTest(value=value),self.assertRaises(ValueError):
                Order().add_item(Product(1,"Coffee",Decimal("80")),value)

    def test_order_rejects_unavailable_product(self):
        with self.assertRaises(ValueError):
            Order().add_item(Product(1,"Coffee",Decimal("80"),False),1)

    def test_amount_validation(self):
        for value in ("NaN","Infinity","-1","1.001","100000000","abc"):
            with self.subTest(value=value),self.assertRaises(ValueError): amount(value)
        self.assertEqual(amount("0"),Decimal("0.00"))

    def test_email_normalization(self):
        self.assertEqual(email_value(" A@Example.com "),"a@example.com")
        with self.assertRaises(ValueError): email_value("not-an-email")

    def test_low_stock_boundary(self):
        self.assertTrue(Ingredient(1,"Milk",Decimal("100"),"ml",Decimal("100")).is_low())

    def test_cash_change_and_underpayment(self):
        cash = CashPayment()
        self.assertEqual(cash.validate(Decimal("250"),Decimal("300")),Decimal("50"))
        with self.assertRaises(ValueError): cash.validate(Decimal("250"),Decimal("200"))

    def test_gcash_reference_and_exact_amount(self):
        gcash = GCashPayment()
        self.assertEqual(gcash.validate(Decimal("100"),Decimal("100"),"ref1"),0)
        with self.assertRaises(ValueError): gcash.validate(Decimal("100"),Decimal("100"),"")
        with self.assertRaises(ValueError): gcash.validate(Decimal("100"),Decimal("101"),"ref1")

    def test_password_hash_verification(self):
        hashed = HASHER.hash("GoodPassword123")
        self.assertNotEqual(hashed,"GoodPassword123")
        self.assertTrue(verify(hashed,"GoodPassword123"))
        self.assertFalse(verify(hashed,"wrong"))
        self.assertFalse(verify("plaintext-legacy","plaintext-legacy"))


if __name__ == "__main__":
    unittest.main()

