import os
import sqlite3
from pathlib import Path

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
DB_PATH = Path(__file__).resolve().parent / "expense.db"
BUDGET_SERVICE_URL = os.environ.get("BUDGET_SERVICE_URL", "http://budget-service:5007")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            amount REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "expense-service"})


@app.post("/expenses")
def add_expense():
    payload = request.get_json(silent=True) or {}
    user_id = str(payload.get("user_id", "guest"))
    title = payload.get("title")
    amount = payload.get("amount")
    budget = payload.get("budget")
    if not title or amount is None:
        return jsonify({"error": "title and amount are required"}), 400

    conn = get_db()
    conn.execute("INSERT INTO expenses(user_id, title, amount) VALUES (?, ?, ?)", (user_id, title, float(amount)))
    conn.commit()
    total = conn.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = ?", (user_id,)).fetchone()["total"]
    conn.close()

    eval_result = {}
    try:
        resp = requests.post(
            f"{BUDGET_SERVICE_URL}/evaluate",
            json={"user_id": user_id, "budget": budget or 0, "total_cost": float(total)},
            timeout=5,
        )
        eval_result = resp.json()
    except requests.RequestException:
        eval_result = {"error": "budget-service unavailable"}

    return jsonify({"total_expense": total, "budget_check": eval_result}), 201


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5006)
