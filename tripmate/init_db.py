from pathlib import Path

from db import get_db


def init_db():
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    conn = get_db()

    with open(schema_path, "r", encoding="utf-8") as schema_file:
        conn.executescript(schema_file.read())

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
