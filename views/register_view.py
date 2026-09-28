import customtkinter as ctk
from views.common import Page, info
from services.auth_service import AuthService


class RegisterView(Page):
    def __init__(self, master, app):
        super().__init__(master,app)
        ctk.CTkLabel(self,text="Create a customer account",font=("Arial",24)).pack(pady=25)
        self.inputs = {}
        for key,label in [("name","Full name"),("email","Email"),("phone","Phone (optional)"),("password","Password (8+ characters)"),("confirm","Repeat password")]:
            widget = ctk.CTkEntry(self,placeholder_text=label,width=400,show="*" if key in ("password","confirm") else "")
            widget.pack(pady=9)
            self.inputs[key] = widget
        ctk.CTkButton(self,text="Register",command=lambda:app.run_action(self.register)).pack(pady=15)
        ctk.CTkButton(self,text="Back to login",command=app.show_login).pack(pady=8)

    def register(self):
        values = {key:widget.get() for key,widget in self.inputs.items()}
        if values["password"] != values["confirm"]:
            raise ValueError("Passwords do not match.")
        AuthService().register(values["name"],values["email"],values["phone"],values["password"])
        info("Account created. You can now log in.")
        self.app.show_login()

