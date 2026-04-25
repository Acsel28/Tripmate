import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
DB_PATH = Path(__file__).resolve().parent / "trip.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            source_city TEXT NOT NULL,
            destination_city TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            budget REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def parse_date(d):
    return datetime.strptime(d, "%Y-%m-%d").date()


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "trip-service"})


@app.post("/trips")
def create_trip():
    payload = request.get_json(silent=True) or {}
    required = ["user_id", "source_city", "destination_city", "start_date", "end_date", "budget"]
    for field in required:
        if field not in payload:
            return jsonify({"error": f"{field} is required"}), 400

    try:
        start = parse_date(payload["start_date"])
        end = parse_date(payload["end_date"])
    except ValueError:
        return jsonify({"error": "invalid date format, use YYYY-MM-DD"}), 400

    if end <= start:
        return jsonify({"error": "end_date must be after start_date"}), 400

    conn = get_db()
    rows = conn.execute("SELECT start_date, end_date FROM trips WHERE user_id = ?", (payload["user_id"],)).fetchall()
    for row in rows:
        existing_start = parse_date(row["start_date"])
        existing_end = parse_date(row["end_date"])
        if not (end < existing_start or start > existing_end):
            conn.close()
            return jsonify({"error": "overlapping trip dates detected"}), 409

    conn.execute(
        """
        INSERT INTO trips (user_id, source_city, destination_city, start_date, end_date, budget)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            payload["user_id"],
            payload["source_city"],
            payload["destination_city"],
            payload["start_date"],
            payload["end_date"],
            float(payload["budget"]),
        ),
    )
    conn.commit()
    trip = conn.execute("SELECT * FROM trips ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return jsonify({"trip": dict(trip)}), 201


@app.get("/trips")
def list_trips():
    user_id = request.args.get("user_id")
    conn = get_db()
    if user_id:
        rows = conn.execute("SELECT * FROM trips WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM trips ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify({"trips": [dict(r) for r in rows]})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5003)
