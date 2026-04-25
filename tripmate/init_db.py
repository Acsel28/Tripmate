from pathlib import Path

from db import get_db


def add_column_if_missing(conn, table_name, column_name, column_definition):
    columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    existing_names = {col[1] for col in columns}
    if column_name not in existing_names:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


def run_non_destructive_migrations(conn):
    add_column_if_missing(conn, "itineraries", "start_date", "TEXT")
    add_column_if_missing(conn, "itineraries", "end_date", "TEXT")

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS booking_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            from_status TEXT,
            to_status TEXT NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'info',
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )


def init_db():
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    conn = get_db()

    with open(schema_path, "r", encoding="utf-8") as schema_file:
        conn.executescript(schema_file.read())

    run_non_destructive_migrations(conn)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
