"""A new connection per transaction; no shared global connection."""
from contextlib import contextmanager
import mysql.connector
from config import DB_CONFIG


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


@contextmanager
def transaction(write=False):
    conn = get_connection()
    cur = None
    try:
        conn.start_transaction(isolation_level="READ COMMITTED")
        cur = conn.cursor(dictionary=True, buffered=True)
        if write:
            # One cafe: serialize application writes to keep stock, account
            # changes, payments and recipe editing consistent across windows.
            cur.execute("SELECT lock_id FROM app_mutex WHERE lock_id=1 FOR UPDATE")
            if cur.fetchone() is None:
                raise RuntimeError("Run setup_db.py before starting BrewHub.")
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cur is not None:
            cur.close()
        conn.close()

