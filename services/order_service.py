from decimal import Decimal
from uuid import UUID
from models.order import Order
from models.product import Product
from repositories.queries import one, all_rows, insert
from services.common import Service, amount, text_value
from services.inventory_service import record_stock

NEXT_STATUS = {"Confirmed":"Preparing", "Preparing":"Ready", "Ready":"Completed"}


class OrderService(Service):
    def _quote(self, cur, cart):
        if not cart:
            raise ValueError("Your cart is empty.")
        order = Order()
        for product_id, quantity in sorted(cart.items()):
            row = one(cur,"SELECT * FROM products WHERE product_id=%s",(product_id,))
            if not row:
                raise ValueError("A product in your cart no longer exists. Remove it and refresh the menu.")
            order.add_item(Product(row["product_id"],row["product_name"],row["price"],bool(row["availability"])),quantity)
        amount(order.calculate_total(),"Order total",True)
        return order

    def quote(self, cart):
        with self.tx("order") as cur:
            return self._quote(cur,cart)

    def place_order(self, cart, request_token, expected_total):
        try:
            request_token = str(UUID(request_token))
        except (ValueError,TypeError,AttributeError):
            raise ValueError("Invalid order request ID.") from None
        with self.tx("order",True) as cur:
            old = one(cur,"SELECT order_id,user_id FROM orders WHERE request_token=%s",(request_token,))
            if old:
                if old["user_id"] != self.user.user_id:
                    raise ValueError("Order request belongs to another account.")
                return old["order_id"]
            order = self._quote(cur,cart)
            if order.calculate_total() != amount(expected_total):
                raise ValueError("Prices changed. Refresh the cart and review the new total before submitting.")
            order_id = insert(cur,"""INSERT INTO orders(user_id,total_amount,status,inventory_deducted,request_token)
                VALUES(%s,%s,'Pending',0,%s)""",(self.user.user_id,order.calculate_total(),request_token))
            for item in order.items:
                cur.execute("""INSERT INTO order_items(order_id,product_id,quantity,unit_price,subtotal,product_name_snapshot)
                    VALUES(%s,%s,%s,%s,%s,%s)""",(order_id,item.product_id,item.quantity,item.unit_price,item.subtotal(),item.product_name))
            return order_id

    def list_orders(self, status="All"):
        with self.tx() as cur:
            sql = """SELECT o.*,u.full_name,COALESCE(p.payment_status,'Unpaid') AS payment_status,
                p.payment_method,p.amount_paid,p.reference_number,p.payment_date
                FROM orders o JOIN users u ON u.user_id=o.user_id
                LEFT JOIN payments p ON p.order_id=o.order_id WHERE 1=1"""
            args = []
            if not self.user.can("manage"):
                sql += " AND o.user_id=%s"
                args.append(self.user.user_id)
            if status != "All":
                sql += " AND o.status=%s"
                args.append(status)
            return all_rows(cur,sql+" ORDER BY o.order_id DESC",tuple(args))

    def _owned(self, cur, order_id):
        order = one(cur,"SELECT * FROM orders WHERE order_id=%s FOR UPDATE",(order_id,))
        if not order or (order["user_id"] != self.user.user_id and not self.user.can("manage")):
            raise ValueError("Order not found or not accessible.")
        return order

    def details(self, order_id):
        with self.tx() as cur:
            order = self._owned(cur,order_id)
            items = all_rows(cur,"""SELECT oi.*,COALESCE(oi.product_name_snapshot,p.product_name) AS product_name
                FROM order_items oi JOIN products p ON p.product_id=oi.product_id
                WHERE oi.order_id=%s ORDER BY oi.order_item_id""",(order_id,))
            payment = one(cur,"SELECT * FROM payments WHERE order_id=%s",(order_id,))
            return order,items,payment

    def confirm(self, order_id):
        with self.tx("manage",True) as cur:
            order = self._owned(cur,order_id)
            if order["status"] != "Pending":
                raise ValueError("Only Pending orders can be confirmed. Refresh the list.")
            if order["inventory_deducted"]:
                raise ValueError("This order already has a stock deduction; review its stock history.")
            items = all_rows(cur,"SELECT * FROM order_items WHERE order_id=%s ORDER BY product_id",(order_id,))
            if not items:
                raise ValueError("This order has no items.")
            needed = {}
            for item in items:
                if item["quantity"] <= 0:
                    raise ValueError("This legacy order contains invalid quantities.")
                product = one(cur,"SELECT * FROM products WHERE product_id=%s",(item["product_id"],))
                if not product or not product["availability"]:
                    raise ValueError("An ordered product is now unavailable.")
                recipe = all_rows(cur,"SELECT * FROM product_ingredients WHERE product_id=%s",(item["product_id"],))
                if not recipe:
                    raise ValueError(f"Add a recipe for {product['product_name']} before confirming. Packaged goods need a piece-count ingredient.")
                for line in recipe:
                    if line["quantity_required"] <= 0:
                        raise ValueError("Recipe quantities must be positive.")
                    iid = line["ingredient_id"]
                    needed[iid] = needed.get(iid,Decimal("0")) + line["quantity_required"]*item["quantity"]
            for iid, quantity in sorted(needed.items()):
                stock = one(cur,"SELECT * FROM ingredients WHERE ingredient_id=%s FOR UPDATE",(iid,))
                if not stock or (stock["quantity"] or 0) < quantity:
                    raise ValueError(f"Insufficient stock: {stock['ingredient_name'] if stock else iid}. Need {quantity}.")
                amount(quantity,"Ingredient requirement",True)
                cur.execute("UPDATE ingredients SET quantity=quantity-%s WHERE ingredient_id=%s",(quantity,iid))
                cur.execute("INSERT INTO order_stock(order_id,ingredient_id,quantity) VALUES(%s,%s,%s)",(order_id,iid,quantity))
                record_stock(cur,iid,"Stock Out",quantity,f"Order #{order_id} confirmed",self.user.user_id,order_id)
            cur.execute("UPDATE orders SET status='Confirmed',inventory_deducted=1 WHERE order_id=%s",(order_id,))

    def advance(self, order_id):
        with self.tx("manage",True) as cur:
            order = self._owned(cur,order_id)
            target = NEXT_STATUS.get(order["status"])
            if not target:
                raise ValueError("Confirm a pending order first, or choose an active order.")
            if order["inventory_deducted"] != 1:
                raise ValueError("Legacy order has unverified stock history. Reconcile it before continuing (see README).")
            if target == "Completed":
                payment = one(cur,"SELECT * FROM payments WHERE order_id=%s",(order_id,))
                if not payment or payment["payment_status"] != "Paid" or payment["amount_paid"] != order["total_amount"]:
                    raise ValueError("Record full payment before completing this order.")
                cur.execute("UPDATE orders SET status=%s,completed_at=NOW() WHERE order_id=%s",(target,order_id))
            else:
                cur.execute("UPDATE orders SET status=%s WHERE order_id=%s",(target,order_id))
            return target

    def cancel(self, order_id, reason):
        reason = text_value(reason,"Cancellation reason",255)
        with self.tx(write=True) as cur:
            order = self._owned(cur,order_id)
            status = order["status"]
            if not self.user.can("manage") and status != "Pending":
                raise ValueError("Customers can cancel Pending orders only.")
            if status in ("Cancelled","Completed"):
                raise ValueError("Completed or cancelled orders cannot be cancelled again.")
            if status not in ("Pending","Confirmed","Preparing","Ready"):
                raise ValueError("Unknown legacy order status; review it before cancellation.")
            if status != "Pending" and order["inventory_deducted"] != 1:
                raise ValueError("Legacy order has unverified stock history. Reconcile it before cancelling.")
            if status == "Confirmed":
                # Preparation has not begun. Restore the original snapshot,
                # even if the recipe has since changed.
                lines = all_rows(cur,"SELECT * FROM order_stock WHERE order_id=%s ORDER BY ingredient_id",(order_id,))
                if not lines:
                    raise ValueError("Missing stock snapshot. Review this legacy order first.")
                for line in lines:
                    cur.execute("UPDATE ingredients SET quantity=quantity+%s WHERE ingredient_id=%s",(line["quantity"],line["ingredient_id"]))
                    record_stock(cur,line["ingredient_id"],"Stock In",line["quantity"],f"Order #{order_id} cancelled before preparation",self.user.user_id,order_id)
            # Preparing/Ready ingredients remain consumed (waste). Payments are
            # not silently refunded: the admin records the actual refund separately.
            cur.execute("UPDATE orders SET status='Cancelled',cancel_reason=%s WHERE order_id=%s",(reason,order_id))

