"""Local settings. Copy config_local.example.py to config_local.py first."""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
DB_CONFIG = {"host": "localhost", "port": 3307, "user": "root",
             "password": "", "database": "brewhub_db", "connection_timeout": 8}
try:
    from config_local import DB_CONFIG as LOCAL_CONFIG
    DB_CONFIG.update(LOCAL_CONFIG)
except ImportError:
    pass
# Used by the isolated test suite; normal users edit config_local.py.
for key in ("host", "port", "user", "password", "database"):
    value = os.getenv("BREWHUB_DB_" + key.upper())
    if value is not None:
        DB_CONFIG[key] = int(value) if key == "port" else value
DB_CONFIG["port"] = int(DB_CONFIG["port"])
DB_CONFIG.update(charset="utf8mb4", collation="utf8mb4_unicode_ci", use_pure=True)
REPORT_DIR = BASE_DIR / "reports"
IMAGE_DIR = BASE_DIR / "assets" / "images"

