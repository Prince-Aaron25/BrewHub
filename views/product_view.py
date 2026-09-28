from tkinter import messagebox
import customtkinter as ctk
from views.common import Page, DataTable, FormDialog, field, info, import_product_image
from services.catalog_service import CatalogService


class ProductView(Page):
    def __init__(self,master,app):
        super().__init__(master,app)
        bar = self.toolbar()
        self.search = ctk.CTkEntry(bar,placeholder_text="Search name")
        self.search.pack(side="left",padx=5)
        for label,fn in [("Refresh",self.refresh),("Add product",lambda:self.edit()),("Edit",lambda:self.edit(self.table.selected())),("Remove",self.remove),("Categories",self.categories_dialog)]:
            self.button(bar,label,fn,width=120)
        self.table = DataTable(self,[("product_id","ID",55),("product_name","Product",180),("category_name","Category",140),("price","PHP",80),("availability","Available (1=yes)",130),("description","Description",220),("image_path","Image",180)])
        self.button(self.toolbar(),"Choose picture for selected product",self.picture,width=280)
        self.note("ADD YOUR PRODUCTS HERE. Leave Image path blank until you choose a picture. Add recipes in the Recipes tab.")

    def refresh(self):
        self.table.load(CatalogService(self.app.user).products(self.search.get(),include_unavailable=True))

    def edit(self,row=None):
        row = row or {}
        service = CatalogService(self.app.user)
        choices = {f"{r['category_id']} - {r['category_name']}":r["category_id"] for r in service.categories()}
        if not choices:
            raise ValueError("Create a category using the Categories button first.")
        initial = next((key for key,value in choices.items() if value==row.get("category_id")),next(iter(choices)))
        fields = [field("name","Product name",row.get("product_name","")),field("category","Category",initial,choices),
            field("description","Description",row.get("description","")),field("price","Price in PHP",row.get("price","")),
            field("image","Image path (optional)",row.get("image_path","")),field("available","Available", "Yes" if row.get("availability",True) else "No",["Yes","No"])]
        def save(v):
            service.save_product(v["name"],choices[v["category"]],v["description"],v["price"],v["image"],v["available"]=="Yes",row.get("product_id"))
            self.refresh()
        FormDialog(self.app,"Product",fields,save)

    def picture(self):
        row = self.table.selected()
        path = import_product_image()
        if path:
            CatalogService(self.app.user).save_product(row["product_name"],row["category_id"],row["description"],row["price"],path,row["availability"],row["product_id"])
            self.refresh()

    def remove(self):
        row = self.table.selected()
        if messagebox.askyesno("Remove product","Unused products are deleted; products with order history become unavailable. Continue?"):
            info(CatalogService(self.app.user).delete_product(row["product_id"]))
            self.refresh()

    def categories_dialog(self):
        window = ctk.CTkToplevel(self.app)
        window.title("Categories")
        window.geometry("650x480")
        window.transient(self.app)
        table = DataTable(window,[("category_id","ID",80),("category_name","Category",350)])
        service = CatalogService(self.app.user)
        def refresh(): table.load(service.categories())
        def edit(row=None):
            row = row or {}
            def save(v):
                service.save_category(v["name"],row.get("category_id"))
                refresh()
                self.refresh()
            FormDialog(self.app,"Category",[field("name","Category name",row.get("category_name",""))],save)
        def remove():
            row = table.selected()
            if messagebox.askyesno("Delete category","Delete this unused category?"):
                service.delete_category(row["category_id"])
                refresh()
        bar = ctk.CTkFrame(window)
        bar.pack(fill="x")
        self.button(bar,"Add",edit)
        self.button(bar,"Edit",lambda:edit(table.selected()))
        self.button(bar,"Delete",remove)
        refresh()

