import os
import sqlite3
from pathlib import Path

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
DB_PATH = Path(__file__).resolve().parent / "budget.db"
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://notification-service:5008")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS budgets (
            user_id TEXT PRIMARY KEY,
            budget REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "budget-service"})


@app.post("/budgets")
def set_budget():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    budget = payload.get("budget")
    if user_id is None or budget is None:
        return jsonify({"error": "user_id and budget are required"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO budgets(user_id, budget) VALUES(?, ?) ON CONFLICT(user_id) DO UPDATE SET budget=excluded.budget",
        (str(user_id), float(budget)),
    )
    conn.commit()
    conn.close()
    return jsonify({"user_id": str(user_id), "budget": float(budget)}), 200


@app.get("/budgets/<user_id>")
def get_budget(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM budgets WHERE user_id = ?", (str(user_id),)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "budget not found"}), 404
    return jsonify(dict(row))


@app.post("/evaluate")
def evaluate_affordability():
    payload = request.get_json(silent=True) or {}
    user_id = str(payload.get("user_id", "guest"))
    total_cost = float(payload.get("total_cost", 0))
    budget_input = payload.get("budget")

    conn = get_db()
    saved = conn.execute("SELECT budget FROM budgets WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()

    budget = float(saved["budget"]) if saved else float(budget_input or 0)
    affordable = total_cost <= budget
    remaining = round(budget - total_cost, 2)

    if not affordable:
        try:
            requests.post(
                f"{NOTIFICATION_SERVICE_URL}/notify",
                json={
                    "user_id": user_id,
                    "level": "warning",
                    "message": f"Budget exceeded by {abs(remaining)}",
                },
                timeout=5,
            )
        except requests.RequestException:
            pass

    return jsonify(
        {
            "budget": budget,
            "total_cost": total_cost,
            "affordable": affordable,
            "remaining": remaining,
            "status": "affordable" if affordable else "not affordable",
        }
    )


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5007)
