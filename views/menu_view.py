from pathlib import Path
import customtkinter as ctk
from PIL import Image
from config import BASE_DIR
from views.common import Page, DataTable, info
from services.catalog_service import CatalogService


class MenuView(Page):
    def __init__(self,master,app):
        super().__init__(master,app)
        bar = self.toolbar()
        self.search = ctk.CTkEntry(bar,placeholder_text="Search products")
        self.search.pack(side="left",padx=4)
        self.category = ctk.CTkComboBox(bar,values=["All categories"],state="readonly",width=210)
        self.category.set("All categories")
        self.category.pack(side="left",padx=4)
        self.button(bar,"Search / Refresh",self.refresh)
        self.categories = {}
        self.table = DataTable(self,[("product_id","ID",60),("product_name","Product",200),("category_name","Category",140),("price","PHP",90),("description","Description",300)],on_select=self.preview)
        bottom = self.toolbar()
        self.quantity = ctk.CTkEntry(bottom,width=90)
        self.quantity.insert(0,"1")
        ctk.CTkLabel(bottom,text="Quantity:").pack(side="left",padx=6)
        self.quantity.pack(side="left",padx=4)
        self.button(bottom,"Add selected to cart",self.add)
        self.preview_label = ctk.CTkLabel(self,text="Select a product to preview its picture.",height=140)
        self.preview_label.pack(pady=6)
        self.note("Orders are pending until the cafe confirms ingredient availability. Pictures are optional.")

    def refresh(self):
        service = CatalogService(self.app.user)
        self.categories = {f"{r['category_id']} - {r['category_name']}":r["category_id"] for r in service.categories()}
        choices = ["All categories"]+list(self.categories)
        current = self.category.get()
        self.category.configure(values=choices)
        if current not in choices:
            self.category.set("All categories")
        self.table.load(service.products(self.search.get(),self.categories.get(self.category.get())))

    def add(self):
        row = self.table.selected()
        try:
            quantity = int(self.quantity.get())
        except ValueError:
            raise ValueError("Quantity must be a whole number.") from None
        if not 1<=quantity<=999:
            raise ValueError("Quantity must be from 1 to 999.")
        old = self.app.cart.get(row["product_id"])
        combined = quantity + (old["quantity"] if old else 0)
        if combined > 999:
            raise ValueError("Maximum 999 per product.")
        self.app.cart[row["product_id"]] = {"name":row["product_name"],"price":row["price"],"quantity":combined}
        self.app.cart_changed()
        info("Added to cart. Open the Cart tab to review and submit.")

    def preview(self):
        try:
            row = self.table.selected()
        except ValueError:
            return
        try:
            path = Path(row.get("image_path") or "")
            if not path.is_absolute():
                path = BASE_DIR/path
            with Image.open(path) as original:
                picture = original.convert("RGB")
                picture.thumbnail((190,140))
                self.picture = ctk.CTkImage(light_image=picture,dark_image=picture,size=picture.size)
            self.preview_label.configure(image=self.picture,text="")
        except (OSError,ValueError):
            self.preview_label.configure(image=None,text="No picture added yet")
