from tkinter import messagebox
import customtkinter as ctk
from views.common import Page, DataTable, FormDialog, field
from services.inventory_service import InventoryService


class InventoryView(Page):
    def __init__(self,master,app):
        super().__init__(master,app)
        bar = self.toolbar()
        self.low = ctk.CTkCheckBox(bar,text="Low stock only",width=140)
        self.low.pack(side="left",padx=6)
        for label,fn in [("Refresh",self.refresh),("Add ingredient",lambda:self.edit()),("Edit",lambda:self.edit(self.table.selected())),("Change stock",self.stock),("History",self.history)]:
            self.button(bar,label,fn,width=120)
        self.table = DataTable(self,[("ingredient_id","ID",60),("ingredient_name","Ingredient",240),("quantity","Current stock",130),("unit","Unit",120),("reorder_level","Reorder level",130),("low_stock","Low stock",100)])
        self.button(self.toolbar(),"Delete unused ingredient",self.remove,width=220)
        self.note("ADD YOUR INGREDIENTS HERE, then Change stock -> Stock In. Adjustment sets the final counted quantity. Use one fixed unit per ingredient; convert liters to ml before entering amounts.")

    def refresh(self):
        self.table.load(InventoryService(self.app.user).ingredients(bool(self.low.get())))

    def edit(self,row=None):
        row = row or {}
        def save(v):
            InventoryService(self.app.user).save_ingredient(v["name"],v["unit"],v["reorder"],row.get("ingredient_id"))
            self.refresh()
        FormDialog(self.app,"Ingredient",[field("name","Ingredient name",row.get("ingredient_name","")),
            field("unit","Unit (fixed after creation)",row.get("unit","")),field("reorder","Low-stock threshold",row.get("reorder_level",0))],save,
            "Initial stock is zero. Use Change stock to record your opening stock.")

    def stock(self):
        row = self.table.selected()
        def save(v):
            InventoryService(self.app.user).adjust(row["ingredient_id"],v["kind"],v["quantity"],v["reason"])
            self.refresh()
        FormDialog(self.app,f"Stock: {row['ingredient_name']}",[
            field("kind","Action",choices=["Stock In","Stock Out","Adjustment"]),field("quantity",f"Quantity in {row['unit']}"),
            field("reason","Reason / delivery note")],save,"Adjustment = final physical count. Stock In/Out = amount to add/remove.")

    def history(self):
        rows = InventoryService(self.app.user).history()
        window = ctk.CTkToplevel(self.app)
        window.geometry("1150x580")
        window.title("Stock movement history")
        table = DataTable(window,[("transaction_id","ID",60),("transaction_date","Date",160),("ingredient_name","Ingredient",170),("transaction_type","Type",110),("quantity","Quantity",90),("unit","Unit",70),("remarks","Reason",240),("performed_by_name","Admin",140)])
        table.load(rows)

    def remove(self):
        row = self.table.selected()
        if messagebox.askyesno("Delete ingredient","Delete this unused ingredient? Stock history and recipes prevent deletion."):
            InventoryService(self.app.user).delete_ingredient(row["ingredient_id"])
            self.refresh()

