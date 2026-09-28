"""Run once after editing config_local.py. Safe to rerun; never drops data.
MySQL DDL commits separately: back up with Workbench before running.
"""
import argparse
from getpass import getpass
from pathlib import Path
import re
import mysql.connector
from config import DB_CONFIG
from database import get_connection, transaction
from services.auth_service import HASHER, password_value
from services.common import text_value, email_value

BASE_COLUMNS = {
 "users": "user_id full_name email password phone role status created_at",
 "categories": "category_id category_name",
 "products": "product_id category_id product_name description price image_path availability",
 "ingredients": "ingredient_id ingredient_name quantity unit reorder_level",
 "product_ingredients": "product_id ingredient_id quantity_required",
 "orders": "order_id user_id order_date total_amount status",
 "order_items": "order_item_id order_id product_id quantity unit_price subtotal",
 "payments": "payment_id order_id payment_method amount_paid payment_status reference_number payment_date",
 "inventory_transactions": "transaction_id ingredient_id transaction_type quantity remarks transaction_date",
}
ADDITIONS = {
 "orders": {"inventory_deducted": "BOOLEAN NULL DEFAULT NULL", "request_token": "VARCHAR(36) NULL",
            "completed_at": "DATETIME NULL", "cancel_reason": "VARCHAR(255) NULL"},
 "order_items": {"product_name_snapshot": "VARCHAR(100) NULL"},
 "payments": {"tendered": "DECIMAL(10,2) NULL", "change_amount": "DECIMAL(10,2) NULL",
              "recorded_by": "INT NULL", "refunded_at": "DATETIME NULL", "refund_reason": "VARCHAR(255) NULL"},
 "inventory_transactions": {"order_id": "INT NULL", "performed_by": "INT NULL"},
}


def migrate():
    name = DB_CONFIG["database"]
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise ValueError("Database name may contain letters, digits and underscores only.")
    options = {k:v for k,v in DB_CONFIG.items() if k != "database"}
    conn = mysql.connector.connect(**options)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{name}` CHARACTER SET utf8mb4")
        cur.execute(f"USE `{name}`")
        # Preflight existing table shapes before any ALTER statement.
        for table, fields in BASE_COLUMNS.items():
            cur.execute("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s", (name,table))
            existing = cur.fetchone()
            if existing:
                if existing["ENGINE"] != "InnoDB":
                    raise ValueError(f"{table} must use InnoDB; ask for migration help before proceeding.")
                cur.execute(f"SHOW COLUMNS FROM `{table}`")
                columns = {r["Field"] for r in cur.fetchall()}
                missing = set(fields.split()) - columns
                if missing:
                    raise ValueError(f"Unexpected schema: {table} is missing {sorted(missing)}. No tables were erased.")
        source = (Path(__file__).parent / "sql/schema.sql").read_text()
        sql = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("--"))
        for statement in sql.split(";"):
            if statement.strip():
                cur.execute(statement)
        for table, additions in ADDITIONS.items():
            cur.execute(f"SHOW COLUMNS FROM `{table}`")
            columns = {r["Field"] for r in cur.fetchall()}
            for column, definition in additions.items():
                if column not in columns:
                    cur.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}")
        # Preserve existing ENUM values while adding required workflow values.
        cur.execute("SHOW COLUMNS FROM orders LIKE 'status'")
        definition = cur.fetchone()["Type"]
        if definition.startswith("enum("):
            existing = re.findall(r"'([^']*)'", definition)
            required = ["Pending","Confirmed","Preparing","Ready","Completed","Cancelled"]
            values = existing + [v for v in required if v not in existing]
            if values != existing:
                if not all(re.fullmatch(r"[A-Za-z ]+", v) for v in values):
                    raise ValueError("Unusual order statuses: review schema manually.")
                quoted = ",".join("'"+v+"'" for v in values)
                cur.execute(f"ALTER TABLE orders MODIFY status ENUM({quoted}) DEFAULT 'Pending'")
        cur.execute("SHOW INDEX FROM orders")
        indexes = cur.fetchall()
        if not any(r["Key_name"] == "uq_order_request" for r in indexes):
            cur.execute("ALTER TABLE orders ADD UNIQUE KEY uq_order_request(request_token)")
        conn.commit()
        cur.close()
        print("Schema ready. Existing rows preserved. No products or ingredients were inserted.")
    finally:
        conn.close()


def create_admin(name, email, password):
    name, email = text_value(name,"Name",100), email_value(email)
    password_value(password)
    with transaction(write=True) as cur:
        cur.execute("SELECT user_id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            raise ValueError("Email already exists. No account was changed; use --reset-password if needed.")
        cur.execute("INSERT INTO users(full_name,email,password,role,status) VALUES(%s,%s,%s,'admin','active')",
                    (name,email,HASHER.hash(password)))
    print("Administrator created. Sign in with the email and password you entered.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema-only", action="store_true")
    parser.add_argument("--reset-password", metavar="EMAIL", help="Local DB-owner recovery; keeps account role and data")
    args = parser.parse_args()
    migrate()
    if args.reset_password:
        email = email_value(args.reset_password)
        new = password_value(getpass("New password (8+ characters): "))
        if getpass("Repeat password: ") != new:
            raise ValueError("Passwords do not match.")
        with transaction(write=True) as cur:
            cur.execute("UPDATE users SET password=%s WHERE email=%s", (HASHER.hash(new),email))
            if cur.rowcount != 1:
                raise ValueError("Email not found.")
        print("Password reset. Role and status preserved.")
    elif not args.schema_only:
        answer = input("Create a NEW admin account? [y/N]: ").strip().lower()
        if answer == "y":
            name, email = input("Admin full name: "), input("Admin email: ")
            password = getpass("Admin password (8+ characters): ")
            if getpass("Repeat password: ") != password:
                raise ValueError("Passwords do not match.")
            create_admin(name,email,password)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, mysql.connector.Error) as exc:
        print(f"Setup stopped: {exc}")
        raise SystemExit(1)
