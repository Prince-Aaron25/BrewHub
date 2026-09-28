from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
from xml.sax.saxutils import escape
import csv
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle
from config import REPORT_DIR
from services.common import Service
from services.order_service import OrderService
from services.inventory_service import InventoryService
from repositories.queries import one, all_rows


def pdf_table(path, title, headers, rows, note=""):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    styles = getSampleStyleSheet()
    # Embed the font shipped with ReportLab so receipts render consistently.
    fonts = Path(reportlab.__file__).parent / "fonts"
    if "BrewHubSans" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("BrewHubSans",str(fonts/"Vera.ttf")))
        pdfmetrics.registerFont(TTFont("BrewHubBold",str(fonts/"VeraBd.ttf")))
    style = styles["BodyText"]
    style.fontName = "BrewHubSans"
    styles["Title"].fontName = "BrewHubBold"
    style.fontSize, style.leading = 8, 11
    def cell(value):
        return Paragraph(escape(str(value if value is not None else "")),style)
    content = [Paragraph(escape(title),styles["Title"]),Spacer(1,12)]
    if note:
        content.extend([Paragraph(escape(note),style),Spacer(1,10)])
    data = [[cell(v) for v in headers]] + [[cell(v) for v in row] for row in rows]
    table = LongTable(data,repeatRows=1,colWidths=[(landscape(A4)[0]-64)/len(headers)]*len(headers))
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#dce9f4")),
        ("GRID",(0,0),(-1,-1),.4,colors.grey),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    content.append(table)
    def footer(canvas, doc):
        canvas.setFont("BrewHubSans",8)
        canvas.drawString(32,18,f"BrewHub | Page {doc.page} | Generated {datetime.now():%Y-%m-%d %H:%M}")
    SimpleDocTemplate(str(path),pagesize=landscape(A4),leftMargin=32,rightMargin=32,topMargin=30,bottomMargin=36).build(content,onFirstPage=footer,onLaterPages=footer)
    return path


def new_report_path(prefix, suffix="pdf"):
    REPORT_DIR.mkdir(parents=True,exist_ok=True)
    return REPORT_DIR / f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}_{uuid4().hex[:6]}.{suffix}"


class ReportService(Service):
    def summary(self):
        with self.tx("reports") as cur:
            return {
                "Customers": one(cur,"SELECT COUNT(*) n FROM users WHERE role='customer'")["n"],
                "Products": one(cur,"SELECT COUNT(*) n FROM products")["n"],
                "Open orders": one(cur,"SELECT COUNT(*) n FROM orders WHERE status IN ('Pending','Confirmed','Preparing','Ready')")["n"],
                "Low-stock ingredients": one(cur,"SELECT COUNT(*) n FROM ingredients WHERE COALESCE(quantity,0)<=COALESCE(reorder_level,0)")["n"],
                "Refunds to return": one(cur,"SELECT COUNT(*) n FROM orders o JOIN payments p ON p.order_id=o.order_id WHERE o.status='Cancelled' AND p.payment_status='Paid'")["n"],
            }

    def sales(self, start, end, grouping="Daily"):
        try:
            first, last = date.fromisoformat(str(start)),date.fromisoformat(str(end))
            if first>last:
                raise ValueError()
            end_exclusive = last+timedelta(days=1)
        except (ValueError,OverflowError):
            raise ValueError("Enter a valid start/end range as YYYY-MM-DD.") from None
        if grouping not in ("Daily","Weekly","Monthly"):
            raise ValueError("Choose Daily, Weekly or Monthly.")
        with self.tx("reports") as cur:
            # One payment per order in the user's schema, so totals are not multiplied by items.
            rows = all_rows(cur,"""SELECT o.order_id,o.total_amount,COALESCE(o.completed_at,o.order_date) AS sold_at,
                p.payment_method FROM orders o JOIN payments p ON p.order_id=o.order_id
                WHERE o.status='Completed' AND p.payment_status='Paid' AND p.amount_paid=o.total_amount
                AND COALESCE(o.completed_at,o.order_date)>=%s AND COALESCE(o.completed_at,o.order_date)<%s
                ORDER BY sold_at,o.order_id""",(first,end_exclusive))
        groups = {}
        for r in rows:
            day = r["sold_at"].date()
            if grouping == "Daily": key = day.isoformat()
            elif grouping == "Weekly": key = (day-timedelta(days=day.weekday())).isoformat()+" (week start)"
            else: key = day.strftime("%Y-%m")
            group = groups.setdefault(key,{"period":key,"orders":0,"sales":Decimal("0.00")})
            group["orders"] += 1
            group["sales"] += r["total_amount"]
        return list(groups.values()),rows

    def export_sales(self, start, end, grouping, file_type="pdf"):
        groups,rows = self.sales(start,end,grouping)
        total = sum((r["sales"] for r in groups),Decimal("0.00"))
        data = [[r["period"],r["orders"],f'{r["sales"]:.2f}'] for r in groups]
        path = new_report_path("sales",file_type)
        headers = ["Period","Completed paid orders","Sales (PHP)"]
        if file_type == "csv":
            with path.open("w",newline="",encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(data)
                writer.writerow(["TOTAL",len(rows),f"{total:.2f}"])
            return path
        return pdf_table(path,"BrewHub Sales Report",headers,data,
            f"{start} to {end}; {grouping}. Total PHP {total:.2f}. Paid, completed orders only. Refunded orders excluded. Legacy completion dates use order date.")

    def export_inventory(self):
        rows = InventoryService(self.user).ingredients()
        return pdf_table(new_report_path("inventory"),"BrewHub Inventory Report",
            ["Ingredient","Quantity","Unit","Reorder level","Status"],
            [[r["ingredient_name"],r["quantity"],r["unit"],r["reorder_level"],"LOW" if r["low_stock"] else "OK"] for r in rows])

    def receipt(self, order_id):
        order,items,payment = OrderService(self.user).details(order_id)
        status = payment["payment_status"] if payment else "Unpaid"
        note = f"Order #{order_id} | Placed {order['order_date']} | {order['status']} | Total PHP {order['total_amount']:.2f} | Payment: {status}."
        if payment:
            note += f" Method: {payment['payment_method']}; amount applied: PHP {payment['amount_paid']}; tendered: {payment.get('tendered')}; change: {payment.get('change_amount')}; reference: {payment.get('reference_number') or '-'}; paid at: {payment.get('payment_date')}."
            if payment["payment_status"] == "Refunded":
                note += f" Refund recorded: {payment.get('refunded_at')}; reason: {payment.get('refund_reason') or '-'}"
        return pdf_table(new_report_path(f"order_{order_id}"),"BrewHub Order Receipt",
            ["Product","Quantity","Unit price (PHP)","Subtotal (PHP)"],
            [[r["product_name"],r["quantity"],r["unit_price"],r["subtotal"]] for r in items],note)
