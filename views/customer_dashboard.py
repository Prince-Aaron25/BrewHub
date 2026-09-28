import customtkinter as ctk
from views.common import Page
from views.menu_view import MenuView
from views.cart_view import CartView
from views.order_view import OrderView
from views.profile_view import ProfileView


class CustomerDashboard(Page):
    def __init__(self,master,app):
        super().__init__(master,app)
        bar = self.toolbar()
        ctk.CTkLabel(bar,text=f"BrewHub | {app.user.full_name}").pack(side="left",padx=12)
        self.button(bar,"Log out",app.logout,width=100)
        self.tabs = ctk.CTkTabview(self,command=self.refresh_current)
        self.tabs.pack(fill="both",expand=True,padx=8,pady=8)
        self.pages = {}
        for label,cls in [("Menu",MenuView),("Cart",CartView),("My orders",OrderView),("Profile",ProfileView)]:
            tab = self.tabs.add(label)
            page = cls(tab,app)
            page.pack(fill="both",expand=True)
            self.pages[label] = page
        self.after(50,self.refresh_current)

    def refresh_current(self):
        self.app.run_action(self.pages[self.tabs.get()].refresh)

# Older imports may refer to this name.
Customer_DashboardView = CustomerDashboard

