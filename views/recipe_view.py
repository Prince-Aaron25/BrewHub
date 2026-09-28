import customtkinter as ctk
from views.common import Page, DataTable, FormDialog, field
from services.catalog_service import CatalogService
from services.inventory_service import InventoryService


class RecipeView(Page):
    def __init__(self,master,app):
        super().__init__(master,app)
        bar = self.toolbar()
        self.products = {}
        self.product = ctk.CTkComboBox(bar,values=[""],state="readonly",width=330,command=lambda _:app.run_action(self.load_recipe))
        self.product.pack(side="left",padx=5)
        self.button(bar,"Refresh",self.refresh,width=110)
        self.button(bar,"Add / update ingredient",self.add,width=220)
        self.button(bar,"Remove line",self.remove,width=120)
        self.table = DataTable(self,[("ingredient_id","ID",70),("ingredient_name","Ingredient",250),("quantity_required","Amount per product",180),("unit","Unit",130)])
        self.note("ENTER YOUR RECIPE HERE: quantities for ONE product. Example: latte = 18 grams coffee + 200 ml milk + 1 piece cup. Packaged products need a stock ingredient measured in pieces.")

    def refresh(self):
        rows = CatalogService(self.app.user).products(include_unavailable=True)
        self.products = {f"{r['product_id']} - {r['product_name']}":r["product_id"] for r in rows}
        old = self.product.get()
        self.product.configure(values=list(self.products) or [""])
        self.product.set(old if old in self.products else next(iter(self.products),""))
        self.load_recipe()

    def product_id(self):
        if self.product.get() not in self.products:
            raise ValueError("Add and select a product first.")
        return self.products[self.product.get()]

    def load_recipe(self):
        self.table.load(CatalogService(self.app.user).recipe(self.product_id()) if self.products else [])

    def add(self):
        pid = self.product_id()
        rows = InventoryService(self.app.user).ingredients()
        choices = {f"{r['ingredient_id']} - {r['ingredient_name']} ({r['unit']})":r["ingredient_id"] for r in rows}
        if not choices:
            raise ValueError("Add ingredients in Inventory first.")
        def save(v):
            CatalogService(self.app.user).save_recipe_line(pid,choices[v["ingredient"]],v["quantity"])
            self.load_recipe()
        FormDialog(self.app,"Recipe ingredient",[field("ingredient","Ingredient",choices=choices),field("quantity","Quantity for ONE product")],save)

    def remove(self):
        CatalogService(self.app.user).remove_recipe_line(self.product_id(),self.table.selected()["ingredient_id"])
        self.load_recipe()

