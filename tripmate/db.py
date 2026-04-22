import os
import sqlite3
from pathlib import Path


def resolve_db_path():
    configured_path = os.environ.get("TRIPMATE_DB_PATH")
    if configured_path:
        return configured_path

    return str(Path(__file__).resolve().parent / "tripmate.db")


def get_db():
    conn = sqlite3.connect(resolve_db_path())
    conn.row_factory = sqlite3.Row
    return conn
