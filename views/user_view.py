from tkinter import messagebox
from views.common import Page, DataTable, FormDialog, field, info
from services.profile_service import ProfileService


class UserView(Page):
    def __init__(self,master,app):
        super().__init__(master,app)
        bar = self.toolbar()
        self.button(bar,"Refresh",self.refresh)
        self.button(bar,"Activate",lambda:self.status("active"))
        self.button(bar,"Deactivate",lambda:self.status("inactive"))
        self.button(bar,"Reset customer password",self.reset,width=220)
        self.table = DataTable(self,[("user_id","ID",60),("full_name","Name",200),("email","Email",250),("phone","Phone",140),("role","Role",100),("status","Status",100)])
        self.note("Accounts are deactivated to preserve order history. Customer registration cannot create admin accounts. Use setup_db.py for admin creation/recovery.")

    def refresh(self):
        self.table.load(ProfileService(self.app.user).users())

    def status(self,status):
        row = self.table.selected()
        if messagebox.askyesno("Account status",f"Set {row['email']} to {status}?"):
            ProfileService(self.app.user).set_status(row["user_id"],status)
            self.refresh()

    def reset(self):
        row = self.table.selected()
        def save(v):
            if v["password"] != v["confirm"]:
                raise ValueError("Passwords do not match.")
            ProfileService(self.app.user).reset_customer_password(row["user_id"],v["password"])
            info("Password reset. Give it to the customer privately so they can change it in Profile.")
        FormDialog(self.app,f"Reset password: {row['email']}",[field("password","New temporary password",hidden=True),field("confirm","Repeat password",hidden=True)],save)

