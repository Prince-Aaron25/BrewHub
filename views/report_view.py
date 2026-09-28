from datetime import date
from decimal import Decimal
import customtkinter as ctk
from views.common import Page, DataTable, saved_file
from services.report_service import ReportService


class ReportView(Page):
    def __init__(self,master,app):
        super().__init__(master,app)
        bar = self.toolbar()
        self.start,self.end = ctk.CTkEntry(bar,width=130),ctk.CTkEntry(bar,width=130)
        self.start.insert(0,date.today().replace(day=1).isoformat())
        self.end.insert(0,date.today().isoformat())
        for text,entry in [("From:",self.start),("To:",self.end)]:
            ctk.CTkLabel(bar,text=text).pack(side="left",padx=4)
            entry.pack(side="left",padx=4)
        self.group = ctk.CTkComboBox(bar,values=["Daily","Weekly","Monthly"],state="readonly",width=120)
        self.group.set("Daily")
        self.group.pack(side="left",padx=4)
        self.button(bar,"Show sales",self.refresh,width=110)
        self.table = DataTable(self,[("period","Period",320),("orders","Completed paid orders",200),("sales","Sales (PHP)",200)])
        self.total = ctk.CTkLabel(self,text="",font=("Arial",20))
        self.total.pack(pady=6)
        actions = self.toolbar()
        self.button(actions,"Sales PDF",lambda:self.export("pdf"))
        self.button(actions,"Sales CSV",lambda:self.export("csv"))
        self.button(actions,"Inventory PDF",lambda:saved_file(ReportService(app.user).export_inventory()))
        self.note("Dates: YYYY-MM-DD. Sales include fully paid, completed orders; refunded orders are excluded. Weeks start Monday. Legacy records without a completion date use their order date.")

    def refresh(self):
        groups,rows = ReportService(self.app.user).sales(self.start.get(),self.end.get(),self.group.get())
        self.table.load(groups)
        total = sum((r["sales"] for r in groups),Decimal("0"))
        self.total.configure(text=f"{len(rows)} orders | Total PHP {total:.2f}")

    def export(self,kind):
        saved_file(ReportService(self.app.user).export_sales(self.start.get(),self.end.get(),self.group.get(),kind))
