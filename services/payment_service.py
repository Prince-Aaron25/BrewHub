from models.payment import CashPayment, GCashPayment
from services.common import Service, amount, text_value
from repositories.queries import one, insert


class PaymentService(Service):
    def record(self, order_id, method, tendered, reference=""):
        if method not in ("Cash","GCash"):
            raise ValueError("Choose Cash or GCash.")
        tendered = amount(tendered,"Amount received",True)
        reference = text_value(reference,"Reference",100,False)
        payment_type = CashPayment() if method == "Cash" else GCashPayment()
        with self.tx("manage",True) as cur:
            order = one(cur,"SELECT * FROM orders WHERE order_id=%s FOR UPDATE",(order_id,))
            if not order or order["status"] not in ("Confirmed","Preparing","Ready"):
                raise ValueError("Payment is allowed for Confirmed, Preparing or Ready orders.")
            old = one(cur,"SELECT * FROM payments WHERE order_id=%s",(order_id,))
            if old and old["payment_status"] in ("Paid","Refunded"):
                raise ValueError("This order already has a recorded payment.")
            change = payment_type.validate(order["total_amount"],tendered,reference)
            if method == "GCash" and one(cur,"SELECT payment_id FROM payments WHERE payment_method='GCash' AND reference_number=%s AND order_id<>%s",(reference,order_id)):
                raise ValueError("That GCash reference was already used for another order.")
            values = (method,order["total_amount"],reference if method == "GCash" else None,tendered,change,self.user.user_id)
            if old:
                cur.execute("""UPDATE payments SET payment_method=%s,amount_paid=%s,reference_number=%s,
                    tendered=%s,change_amount=%s,recorded_by=%s,payment_status='Paid',payment_date=NOW()
                    WHERE order_id=%s""",values+(order_id,))
            else:
                insert(cur,"""INSERT INTO payments(payment_method,amount_paid,reference_number,tendered,change_amount,
                    recorded_by,payment_status,payment_date,order_id) VALUES(%s,%s,%s,%s,%s,%s,'Paid',NOW(),%s)""",values+(order_id,))
            return change

    def refund(self, order_id, reason):
        reason = text_value(reason,"Refund reason",255)
        with self.tx("manage",True) as cur:
            order = one(cur,"SELECT * FROM orders WHERE order_id=%s FOR UPDATE",(order_id,))
            if not order or order["status"] not in ("Cancelled","Completed"):
                raise ValueError("Cancel the order first, or choose a completed order.")
            payment = one(cur,"SELECT * FROM payments WHERE order_id=%s",(order_id,))
            if not payment or payment["payment_status"] != "Paid":
                raise ValueError("No paid amount is available to refund.")
            cur.execute("UPDATE payments SET payment_status='Refunded',refunded_at=NOW(),refund_reason=%s WHERE order_id=%s",(reason,order_id))
            return payment["amount_paid"]

