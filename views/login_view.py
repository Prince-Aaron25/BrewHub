import customtkinter as ctk
from views.common import Page
from services.auth_service import AuthService


class LoginView(Page):
    def __init__(self, master, app):
        super().__init__(master,app)
        box = ctk.CTkFrame(self,width=460)
        box.pack(pady=90,padx=30)
        ctk.CTkLabel(box,text="BrewHub",font=("Arial",30,"bold")).pack(padx=80,pady=24)
        ctk.CTkLabel(box,text="Sign in using your email address").pack(pady=5)
        self.email = ctk.CTkEntry(box,placeholder_text="Email",width=330)
        self.email.pack(padx=35,pady=10)
        self.password = ctk.CTkEntry(box,placeholder_text="Password",show="*",width=330)
        self.password.pack(padx=35,pady=10)
        ctk.CTkButton(box,text="Log in",width=330,command=lambda:app.run_action(self.login)).pack(pady=12)
        ctk.CTkButton(box,text="Create customer account",width=330,command=app.show_register).pack(pady=(0,24))
        self.password.bind("<Return>",lambda event:app.run_action(self.login))
        self.note("First use: run setup_db.py to prepare the database and create your admin account.")

    def login(self):
        user = AuthService().login(self.email.get(),self.password.get())
        self.app.signed_in(user)

