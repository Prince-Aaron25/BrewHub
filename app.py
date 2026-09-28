from uuid import uuid4
from pathlib import Path
import logging
import customtkinter as ctk
import mysql.connector
from tkinter import messagebox
from config import BASE_DIR

class BrewHubApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # DESIGN LATER: edit these appearance settings and view widgets.
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title("BrewHub - Cafe Ordering and Inventory")
        self.geometry("1240x820")
        self.minsize(1000,700)
        self.current_frame = None
        self.user = None
        self.cart = {}
        self.cart_token = str(uuid4())
        (BASE_DIR/"logs").mkdir(exist_ok=True)
        logging.basicConfig(filename=str(BASE_DIR/"logs/app.log"),level=logging.ERROR)
        self.show_login()

    def run_action(self, function):
        try:
            return function()
        except ValueError as exc:
            messagebox.showerror("Check your input",str(exc),parent=self)
        except mysql.connector.Error as exc:
            messagebox.showerror("Database unavailable",
                f"Database operation failed (code {exc.errno}). Check MySQL is running, config_local.py and setup_db.py. "
                "Refresh the records before retrying; do not create a new order if it already appears in history.",parent=self)
        except OSError as exc:
            messagebox.showerror("File error",str(exc),parent=self)
        except Exception:
            logging.exception("Unexpected application error")
            messagebox.showerror("Unexpected error","See logs/app.log for details. Please send the error text for troubleshooting.",parent=self)

    def report_callback_exception(self, exc_type, exc_value, traceback):
        logging.error("Tk callback failed",exc_info=(exc_type,exc_value,traceback))
        messagebox.showerror("Unexpected error",str(exc_value),parent=self)

    def switch(self, frame_class):
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame_class(self,self)
        self.current_frame.pack(fill="both",expand=True)

    def show_login(self):
        from views.login_view import LoginView
        self.switch(LoginView)

    def show_register(self):
        from views.register_view import RegisterView
        self.switch(RegisterView)

    def signed_in(self, user):
        self.user = user
        self.cart.clear()
        self.cart_token = str(uuid4())
        if user.can("manage"):
            from views.admin_dashboard import AdminDashboard
            self.switch(AdminDashboard)
        else:
            from views.customer_dashboard import CustomerDashboard
            self.switch(CustomerDashboard)

    def logout(self):
        if self.cart and not messagebox.askyesno("Log out","Your unsent cart will be cleared. Log out?",parent=self):
            return
        self.user = None
        self.cart.clear()
        self.cart_token = str(uuid4())
        self.show_login()

    def cart_changed(self):
        self.cart_token = str(uuid4())

