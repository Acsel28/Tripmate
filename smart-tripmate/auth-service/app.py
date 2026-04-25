import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
DB_PATH = Path(__file__).resolve().parent / "auth.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "auth-service"})


@app.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    conn = get_db()
    try:
        conn.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "email already exists"}), 409

    user = conn.execute("SELECT id, email FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return jsonify(dict(user)), 201


@app.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    password = payload.get("password")

    conn = get_db()
    user = conn.execute("SELECT id, email FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "invalid credentials"}), 401
    return jsonify({"token": f"demo-token-{user['id']}", "user": dict(user)}), 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001)
