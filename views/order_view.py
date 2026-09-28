from tkinter import messagebox
import customtkinter as ctk
from views.common import Page, DataTable, FormDialog, field, info, saved_file
from services.order_service import OrderService
from services.payment_service import PaymentService
from services.report_service import ReportService


class OrderView(Page):
    def __init__(self,master,app):
        super().__init__(master,app)
        bar = self.toolbar()
        self.status = ctk.CTkComboBox(bar,values=["All","Pending","Confirmed","Preparing","Ready","Completed","Cancelled"],state="readonly",width=170)
        self.status.set("All")
        self.status.pack(side="left",padx=5)
        self.button(bar,"Refresh",self.refresh,width=110)
        self.button(bar,"Details",self.details,width=110)
        self.button(bar,"PDF receipt",self.receipt,width=120)
        self.button(bar,"Cancel order",self.cancel,width=120)
        self.table = DataTable(self,[("order_id","Order",65),("order_date","Placed",160),("full_name","Customer",180),("total_amount","PHP",90),("status","Order status",120),("payment_status","Payment",100),("payment_method","Method",90)])
        if app.user.can("manage"):
            controls = self.toolbar()
            for label,fn in [("Confirm + deduct stock",self.confirm),("Next status",self.advance),("Record payment",self.payment),("Record full refund",self.refund)]:
                self.button(controls,label,fn,width=185)
            self.note("Workflow: Pending -> Confirmed -> Preparing -> Ready -> Completed. Full payment is required to complete. Cancelled paid orders need a separate actual refund. Refresh to see other users' changes.")
        else:
            self.note("You may cancel Pending orders only. Refresh to see status updates. Pay at the cafe; admin verifies Cash/GCash payments.")

    def refresh(self):
        self.table.load(OrderService(self.app.user).list_orders(self.status.get()))

    def selected_id(self):
        return self.table.selected()["order_id"]

    def details(self):
        oid = self.selected_id()
        order,items,payment = OrderService(self.app.user).details(oid)
        window = ctk.CTkToplevel(self.app)
        window.geometry("980x650")
        window.title(f"Order #{oid}")
        text = f"Order #{oid} | {order['status']} | Total PHP {order['total_amount']:.2f}"
        if payment:
            text += f"\n{payment['payment_status']} | {payment['payment_method']} | Applied PHP {payment['amount_paid']} | Reference {payment['reference_number'] or '-'}"
            text += f"\nReceived: {payment.get('tendered')} | Change: {payment.get('change_amount')} | Date: {payment.get('payment_date')}"
            if payment.get("refund_reason"):
                text += f"\nRefund: {payment['refund_reason']} at {payment.get('refunded_at')}"
        else:
            text += "\nPayment: Unpaid"
        if order.get("cancel_reason"):
            text += "\nCancellation: "+order["cancel_reason"]
        ctk.CTkLabel(window,text=text,wraplength=900,justify="left").pack(padx=15,pady=15)
        table = DataTable(window,[("product_name","Product",350),("quantity","Quantity",120),("unit_price","PHP/unit",120),("subtotal","Subtotal",140)])
        table.load(items)

    def confirm(self):
        oid = self.selected_id()
        if messagebox.askyesno("Confirm order",f"Confirm order #{oid} and deduct recipe ingredients?"):
            OrderService(self.app.user).confirm(oid)
            self.refresh()

    def advance(self):
        row = self.table.selected()
        if messagebox.askyesno("Advance order",f"Move order #{row['order_id']} from {row['status']} to its next step?"):
            status = OrderService(self.app.user).advance(row["order_id"])
            self.refresh()
            info(f"Order is now {status}.")

    def cancel(self):
        oid = self.selected_id()
        def save(v):
            OrderService(self.app.user).cancel(oid,v["reason"])
            self.refresh()
            info("Order cancelled. If it was paid, the admin must return the money and record the refund separately.")
        FormDialog(self.app,f"Cancel #{oid}",[field("reason","Reason")],save,
            "Before preparation: deducted ingredients are restored. After preparation starts: ingredients stay consumed. Money is not transferred by this app.")

    def payment(self):
        row = self.table.selected()
        def save(v):
            if v["verified"] != "Yes - received and verified":
                raise ValueError("Confirm that the money was received before recording payment.")
            change = PaymentService(self.app.user).record(row["order_id"],v["method"],v["amount"],v["reference"])
            self.refresh()
            info(f"Payment recorded. Cash change: PHP {change:.2f}")
        FormDialog(self.app,f"Payment for order #{row['order_id']}",[
            field("method","Payment method",choices=["Cash","GCash"]),field("amount","Amount received / tendered",row["total_amount"]),
            field("reference","GCash reference (required for GCash)"),
            field("verified","Have you received the cash or verified GCash in your account?",choices=["Not yet","Yes - received and verified"])],save,
            "Full payments only. GCash must match the order total. This records an external payment; it does not contact GCash.")

    def refund(self):
        oid = self.selected_id()
        def save(v):
            if v["returned"] != "Yes - money returned":
                raise ValueError("Return the money before recording its refund.")
            refunded = PaymentService(self.app.user).refund(oid,v["reason"])
            self.refresh()
            info(f"Full refund recorded: PHP {refunded:.2f}")
        FormDialog(self.app,f"Record actual refund for #{oid}",[field("reason","Refund reason"),
            field("returned","Have you returned the full payment?",choices=["Not yet","Yes - money returned"])],save,
            "Cancelled or completed orders only. This records a full refund and does not transfer money or restore prepared ingredients.")

    def receipt(self):
        saved_file(ReportService(self.app.user).receipt(self.selected_id()))
