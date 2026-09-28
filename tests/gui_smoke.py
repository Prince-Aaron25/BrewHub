"""Optional real-window smoke check: py -m tests.gui_smoke.
Requires the same isolated DB environment as integration tests and a display.
Creates test records, opens screens, exercises checkout/admin actions, then cleans up.
"""
import os
import time
from pathlib import Path
from unittest.mock import patch
import customtkinter as ctk
from tests.test_integration import IntegrationTests
from services.order_service import OrderService
from services.payment_service import PaymentService
from services.report_service import ReportService
from views.common import FormDialog, field
from app import BrewHubApp


def main():
    if os.getenv("BREWHUB_RUN_DB_TESTS") != "1":
        raise RuntimeError("Enable the separate test database first; see README.")
    IntegrationTests.setUpClass()
    case = IntegrationTests("test_full_cash_workflow_and_report")
    case.setUp()
    errors = []
    app = None
    try:
        with patch("tkinter.messagebox.showinfo"),patch("tkinter.messagebox.askyesno",return_value=True),patch("tkinter.messagebox.showerror",side_effect=lambda *a,**k:errors.append(a)):
            app = BrewHubApp()
            def pump():
                for _ in range(4): app.update();time.sleep(.05)
            def select_first(table):
                children = table.tree.get_children()
                assert children,"Expected a populated table"
                table.tree.selection_set(children[0])
                table.tree.focus(children[0])
                pump()
            def screenshot(name):
                target = os.getenv("BREWHUB_SCREENSHOTS")
                if target:
                    from PIL import ImageGrab
                    Path(target).mkdir(parents=True,exist_ok=True)
                    ImageGrab.grab(xdisplay=os.getenv("DISPLAY") or None).save(Path(target)/(name+".png"))
            pump()
            screenshot("login")
            app.show_register();pump()
            app.show_login();pump()
            app.current_frame.email.insert(0,case.customer.email)
            app.current_frame.password.insert(0,"TestPass123")
            app.current_frame.login();pump()
            dashboard = app.current_frame
            for label,page in dashboard.pages.items():
                dashboard.tabs.set(label);page.refresh();pump()
            menu = dashboard.pages["Menu"]
            dashboard.tabs.set("Menu");menu.refresh();select_first(menu.table)
            menu.add()
            cart = dashboard.pages["Cart"]
            dashboard.tabs.set("Cart");cart.refresh();pump();screenshot("customer_cart")
            cart.submit();pump()
            assert not app.cart,"Cart should clear after success"
            order_page = dashboard.pages["My orders"]
            dashboard.tabs.set("My orders");order_page.refresh();select_first(order_page.table)
            oid = order_page.selected_id()
            order_page.details();pump()
            for child in app.winfo_children():
                if child.winfo_class()=="Toplevel": child.destroy()
            app.logout();pump()
            app.current_frame.email.insert(0,case.admin.email)
            app.current_frame.password.insert(0,"TestPass123")
            app.current_frame.login();pump()
            dashboard = app.current_frame
            for label,page in dashboard.pages.items():
                dashboard.tabs.set(label);page.refresh();pump()
            products = dashboard.pages["Products"]
            dashboard.tabs.set("Products");products.refresh();select_first(products.table)
            products.edit(products.table.selected());pump()
            # Submit the unchanged edit form to verify dialog mapping and button callback.
            dialogs = [w for w in app.winfo_children() if isinstance(w,FormDialog)]
            assert dialogs
            for widget in dialogs[-1].winfo_children():
                if isinstance(widget,ctk.CTkButton) and widget.cget("text")=="Save / Confirm":
                    widget.invoke()
                    break
            pump()
            admin_orders = dashboard.pages["Orders & payments"]
            dashboard.tabs.set("Orders & payments");admin_orders.refresh();select_first(admin_orders.table)
            admin_orders.confirm();admin_orders.refresh();select_first(admin_orders.table)
            PaymentService(case.admin).record(oid,"Cash",150)
            for _ in range(3):
                admin_orders.refresh();select_first(admin_orders.table);admin_orders.advance()
            admin_orders.refresh();pump();screenshot("admin_orders")
            report = dashboard.pages["Reports"]
            dashboard.tabs.set("Reports");report.refresh();pump();screenshot("reports")
            for path in [ReportService(case.admin).export_sales(report.start.get(),report.end.get(),"Daily"),
                         ReportService(case.admin).export_inventory(),ReportService(case.customer).receipt(oid)]:
                if os.getenv("BREWHUB_SCREENSHOTS"):
                    import shutil
                    shutil.copy2(path,Path(os.environ["BREWHUB_SCREENSHOTS"])/path.name)
                path.unlink()
            assert not errors,f"GUI errors: {errors}"
            print("GUI smoke passed: login/register, all customer/admin tabs, cart submission, product edit, order workflow, report exports.")
    finally:
        if app is not None: app.destroy()
        case.tearDown()


if __name__ == "__main__":
    main()
