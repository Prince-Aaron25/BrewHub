import os
import unittest
from uuid import uuid4
from pathlib import Path
import mysql.connector
from config import DB_CONFIG
from setup_db import migrate


@unittest.skipUnless(os.getenv("BREWHUB_RUN_DB_TESTS")=="1","Opt-in MySQL migration test")
class MigrationTests(unittest.TestCase):
    def test_populated_screenshot_schema_preserved(self):
        if DB_CONFIG["database"] != "brewhub_test_db":
            raise RuntimeError("Use brewhub_test_db for tests.")
        original = DB_CONFIG["database"]
        name = "brewhub_migration_test_"+uuid4().hex[:12]
        conn = mysql.connector.connect(**{k:v for k,v in DB_CONFIG.items() if k!="database"})
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(f"CREATE DATABASE `{name}`")
            cur.execute(f"USE `{name}`")
            source = (Path(__file__).parents[1]/"sql/schema.sql").read_text()
            source = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("--"))
            for statement in source.split(";"):
                if statement.strip(): cur.execute(statement)
            cur.execute("INSERT INTO users(full_name,email,password) VALUES('Existing User','old@example.test','old-hash-kept')")
            uid=cur.lastrowid
            cur.execute("INSERT INTO orders(user_id,total_amount,status) VALUES(%s,120,'Completed')",(uid,))
            oid=cur.lastrowid
            conn.commit()
            DB_CONFIG["database"]=name
            migrate()
            migrate()
            cur.execute("SELECT * FROM users WHERE user_id=%s",(uid,))
            self.assertEqual(cur.fetchone()["password"],"old-hash-kept")
            cur.execute("SELECT * FROM orders WHERE order_id=%s",(oid,))
            row=cur.fetchone()
            self.assertEqual(row["status"],"Completed")
            self.assertEqual(row["total_amount"],120)
            self.assertIsNone(row["inventory_deducted"])
            self.assertIsNone(row["request_token"])
        finally:
            DB_CONFIG["database"]=original
            cur.execute(f"DROP DATABASE IF EXISTS `{name}`")
            cur.close();conn.close()

