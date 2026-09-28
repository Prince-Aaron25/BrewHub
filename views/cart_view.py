from decimal import Decimal
from tkinter import messagebox
import customtkinter as ctk
from views.common import Page, DataTable, FormDialog, field, info
from services.order_service import OrderService


class CartView(Page):
    def __init__(self,master,app):
        super().__init__(master,app)
        bar = self.toolbar()
        self.button(bar,"Refresh prices",self.refresh)
        self.button(bar,"Change quantity",self.edit)
        self.button(bar,"Remove selected",self.remove)
        self.button(bar,"Clear cart",self.clear)
        self.table = DataTable(self,[("product_id","ID",60),("name","Product",300),("quantity","Quantity",100),("price","Price (PHP)",130),("subtotal","Subtotal (PHP)",150)])
        self.total = ctk.CTkLabel(self,text="Total: PHP 0.00",font=("Arial",22))
        self.total.pack(pady=10)
        self.submit_button = self.button(self.toolbar(),"Submit order",self.submit,width=190)
        self.note("Payment will be recorded by the admin after confirmation. GCash is verified manually; this app does not transfer money.")

    def refresh(self):
        # Always show saved cart contents so unavailable items can still be removed.
        self.draw()
        if self.app.cart:
            quote = OrderService(self.app.user).quote({pid:r["quantity"] for pid,r in self.app.cart.items()})
            for item in quote.items:
                self.app.cart[item.product_id].update(price=item.unit_price,name=item.product_name)
            self.draw()

    def draw(self):
        rows = [{"product_id":pid,**r,"subtotal":r["price"]*r["quantity"]} for pid,r in self.app.cart.items()]
        self.table.load(rows)
        self.quoted_total = sum((r["subtotal"] for r in rows),Decimal("0.00"))
        self.total.configure(text=f"Total: PHP {self.quoted_total:.2f}")

    def edit(self):
        row = self.table.selected()
        def save(v):
            try: quantity = int(v["quantity"])
            except ValueError: raise ValueError("Use a whole number.") from None
            if not 1<=quantity<=999: raise ValueError("Use 1 to 999.")
            self.app.cart[row["product_id"]]["quantity"] = quantity
            self.app.cart_changed()
            self.draw()
        FormDialog(self.app,"Cart quantity",[field("quantity","Quantity",row["quantity"])],save)

    def remove(self):
        self.app.cart.pop(self.table.selected()["product_id"])
        self.app.cart_changed()
        self.draw()

    def clear(self):
        if messagebox.askyesno("Clear cart","Remove all cart items?"):
            self.app.cart.clear()
            self.app.cart_changed()
            self.draw()

    def submit(self):
        if not self.app.cart:
            raise ValueError("Your cart is empty.")
        if not messagebox.askyesno("Place order",f"Submit this order for PHP {self.quoted_total:.2f}?"):
            return
        self.submit_button.configure(state="disabled")
        try:
            order_id = OrderService(self.app.user).place_order(
                {pid:r["quantity"] for pid,r in self.app.cart.items()},self.app.cart_token,self.quoted_total)
            self.app.cart.clear()
            self.app.cart_changed()
            self.draw()
            info(f"Order #{order_id} submitted. Open My orders to track it.")
        finally:
            self.submit_button.configure(state="normal")

