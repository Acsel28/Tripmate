import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
DB_PATH = Path(__file__).resolve().parent / "notification.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            level TEXT NOT NULL,
            message TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "notification-service"})


@app.post("/notify")
def notify():
    payload = request.get_json(silent=True) or {}
    user_id = str(payload.get("user_id", "guest"))
    level = payload.get("level", "info")
    message = payload.get("message")
    if not message:
        return jsonify({"error": "message required"}), 400

    conn = get_db()
    conn.execute("INSERT INTO notifications(user_id, level, message) VALUES (?, ?, ?)", (user_id, level, message))
    conn.commit()
    conn.close()
    return jsonify({"status": "sent"}), 201


@app.get("/notifications")
def notifications():
    user_id = request.args.get("user_id")
    conn = get_db()
    if user_id:
        rows = conn.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC LIMIT 20", (user_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    return jsonify({"notifications": [dict(r) for r in rows]})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5008)
