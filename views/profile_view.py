import customtkinter as ctk
from views.common import Page, FormDialog, field, info
from services.profile_service import ProfileService


class ProfileView(Page):
    def __init__(self,master,app):
        super().__init__(master,app)
        ctk.CTkLabel(self,text="My profile",font=("Arial",24)).pack(pady=16)
        self.entries = {}
        for key,label in [("full_name","Full name"),("email","Email"),("phone","Phone")]:
            ctk.CTkLabel(self,text=label).pack()
            entry = ctk.CTkEntry(self,width=450)
            entry.pack(pady=8)
            self.entries[key] = entry
        bar = self.toolbar()
        self.button(bar,"Refresh",self.refresh)
        self.button(bar,"Save profile",self.save)
        self.button(bar,"Change password",self.password)

    def refresh(self):
        row = ProfileService(self.app.user).get_profile()
        for key,entry in self.entries.items():
            entry.delete(0,"end")
            entry.insert(0,row.get(key) or "")

    def save(self):
        ProfileService(self.app.user).update(*(self.entries[key].get() for key in ("full_name","email","phone")))
        info("Profile saved. The greeting updates on your next login.")

    def password(self):
        def save(v):
            if v["new"] != v["confirm"]:
                raise ValueError("New passwords do not match.")
            ProfileService(self.app.user).change_password(v["current"],v["new"])
            info("Password changed.")
        FormDialog(self.app,"Change password",[field("current","Current password",hidden=True),
            field("new","New password (8+ characters)",hidden=True),field("confirm","Repeat new password",hidden=True)],save)

