import customtkinter as ctk
from views.common import Page
from views.product_view import ProductView
from views.recipe_view import RecipeView
from views.inventory_view import InventoryView
from views.order_view import OrderView
from views.report_view import ReportView
from views.user_view import UserView
from views.profile_view import ProfileView
from services.report_service import ReportService


class Overview(Page):
    def __init__(self,master,app):
        super().__init__(master,app)
        self.button(self.toolbar(),"Refresh",self.refresh)
        self.label = ctk.CTkLabel(self,text="",font=("Arial",22),justify="left")
        self.label.pack(pady=35)
        self.note("First setup: Categories -> Ingredients + stock -> Products -> Recipes. Then test a customer order.")

    def refresh(self):
        summary = ReportService(self.app.user).summary()
        self.label.configure(text="\n\n".join(f"{key}: {value}" for key,value in summary.items()))


class AdminDashboard(Page):
    def __init__(self,master,app):
        super().__init__(master,app)
        bar = self.toolbar()
        ctk.CTkLabel(bar,text=f"BrewHub Admin | {app.user.full_name}").pack(side="left",padx=12)
        self.button(bar,"Log out",app.logout,width=100)
        self.tabs = ctk.CTkTabview(self,command=self.refresh_current)
        self.tabs.pack(fill="both",expand=True,padx=8,pady=8)
        self.pages = {}
        for label,cls in [("Overview",Overview),("Products",ProductView),("Recipes",RecipeView),("Inventory",InventoryView),
                          ("Orders & payments",OrderView),("Reports",ReportView),("Users",UserView),("Profile",ProfileView)]:
            tab = self.tabs.add(label)
            page = cls(tab,app)
            page.pack(fill="both",expand=True)
            self.pages[label] = page
        self.after(50,self.refresh_current)

    def refresh_current(self):
        self.app.run_action(self.pages[self.tabs.get()].refresh)

