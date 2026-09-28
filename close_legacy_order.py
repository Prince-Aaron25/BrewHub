"""Optional recovery for pre-existing active orders without stock snapshots.
Does not guess old stock usage, move money, delete history, or alter quantities.
Use only after physically checking stock; record any stock correction in Inventory.
"""
from getpass import getpass
from services.auth_service import AuthService
from services.common import Service, text_value
from repositories.queries import one


def main():
    admin = AuthService().login(input("Admin email: "),getpass("Admin password: "))
    if not admin.can("manage"):
        raise ValueError("Admin access required.")
    order_id = int(input("Legacy order ID to close as Cancelled: "))
    reason = text_value(input("Reason / stock reconciliation note: "),"Reason",200)
    print("This does NOT change stock or return money. Check physical stock and record corrections separately.")
    if input(f"Type CLOSE {order_id} to proceed: ") != f"CLOSE {order_id}":
        print("No changes.");return
    with Service(admin).tx("manage",True) as cur:
        row = one(cur,"SELECT * FROM orders WHERE order_id=%s FOR UPDATE",(order_id,))
        if not row or row["request_token"] is not None or row["inventory_deducted"] is not None:
            raise ValueError("Only legacy orders with unknown stock history can use this tool.")
        if row["status"] in ("Completed","Cancelled"):
            raise ValueError("This order is already closed.")
        cur.execute("UPDATE orders SET status='Cancelled',cancel_reason=%s WHERE order_id=%s",("Legacy reconciliation: "+reason,order_id))
    print("Legacy order closed. If it was paid, return the money and use Record full refund in Orders & payments.")


if __name__ == "__main__":
    main()

