import os
from datetime import datetime

import requests
from flask import Flask, jsonify, redirect, request

from db import get_db
from gateway_routes import auth as auth_routes, budget as budget_routes, reports as reports_routes

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = os.environ.get("TRIPMATE_SECRET_KEY", "tripmate-secret-key-change-in-production")

PUBLIC_GATEWAY_URL = os.environ.get("PUBLIC_GATEWAY_URL", "http://localhost:8000")
PUBLIC_AUTH_URL = os.environ.get("PUBLIC_AUTH_URL", "http://localhost:8001")
PUBLIC_TRAVEL_URL = os.environ.get("PUBLIC_TRAVEL_URL", "http://localhost:8002")
PUBLIC_FINANCE_URL = os.environ.get("PUBLIC_FINANCE_URL", "http://localhost:8003")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:8004")
REQUEST_TIMEOUT_SECONDS = float(os.environ.get("INTERNAL_API_TIMEOUT_SECONDS", "5"))

app.register_blueprint(auth_routes.bp)
app.register_blueprint(budget_routes.bp)
app.register_blueprint(reports_routes.bp)


@app.context_processor
def inject_nav_urls():
    return {
        "nav_urls": {
            "dashboard": f"{PUBLIC_GATEWAY_URL}/dashboard",
            "itinerary": f"{PUBLIC_TRAVEL_URL}/itinerary/",
            "booking": f"{PUBLIC_TRAVEL_URL}/booking/",
            "budget": f"{PUBLIC_FINANCE_URL}/budget/",
            "reports": f"{PUBLIC_FINANCE_URL}/reports/",
            "logout": f"{PUBLIC_AUTH_URL}/auth/logout",
        }
    }


@app.get("/")
def root():
    return redirect("/budget/")


def row_to_dict(row):
    return dict(row) if row else None


def parse_iso_date(raw_value):
    if not isinstance(raw_value, str):
        return None
    try:
        return datetime.strptime(raw_value, "%Y-%m-%d").date()
    except ValueError:
        return None


def send_notification(user_id, event_type, title, message, severity="info"):
    try:
        requests.post(
            f"{NOTIFICATION_SERVICE_URL}/api/notifications",
            json={
                "user_id": user_id,
                "event_type": event_type,
                "severity": severity,
                "title": title,
                "message": message,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        # Keep budget operations resilient even if notifications are unavailable.
        pass


def compute_budget_snapshot(conn, user_id):
    budget = conn.execute("SELECT * FROM budgets WHERE user_id = ?", (user_id,)).fetchone()
    expenses = []
    total_expenses = 0
    remaining = 0

    if budget:
        expenses = conn.execute(
            "SELECT * FROM expenses WHERE budget_id = ? ORDER BY date DESC", (budget["id"],)
        ).fetchall()
        total = conn.execute(
            "SELECT SUM(amount) as total FROM expenses WHERE budget_id = ?", (budget["id"],)
        ).fetchone()
        total_expenses = total["total"] if total and total["total"] else 0
        remaining = float(budget["total_budget"]) - float(total_expenses)

    return budget, expenses, total_expenses, remaining


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "finance"})


@app.get("/api/budget")
def get_budget():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db()
    budget, expenses, total_expenses, remaining = compute_budget_snapshot(conn, user_id)

    conn.close()

    return jsonify(
        {
            "budget": row_to_dict(budget),
            "expenses": [dict(row) for row in expenses],
            "total_expenses": total_expenses,
            "remaining": remaining,
        }
    )


@app.post("/api/budget")
def set_budget():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    total_budget = payload.get("total_budget")

    if not user_id or total_budget in (None, ""):
        return jsonify({"error": "user_id and total_budget are required"}), 400

    try:
        total_budget_value = float(total_budget)
    except (TypeError, ValueError):
        return jsonify({"error": "total_budget must be a valid number"}), 400

    if total_budget_value <= 0:
        return jsonify({"error": "total_budget must be greater than 0"}), 400

    conn = get_db()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT * FROM budgets WHERE user_id = ?", (user_id,)).fetchone()

    if existing:
        cursor.execute("UPDATE budgets SET total_budget = ? WHERE user_id = ?", (total_budget_value, user_id))
    else:
        cursor.execute("INSERT INTO budgets (user_id, total_budget) VALUES (?, ?)", (user_id, total_budget_value))

    conn.commit()
    budget = cursor.execute("SELECT * FROM budgets WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()

    return jsonify({"budget": row_to_dict(budget)}), 200


@app.post("/api/expenses")
def add_expense():
    payload = request.get_json(silent=True) or {}

    user_id = payload.get("user_id")
    category = payload.get("category")
    amount = payload.get("amount")
    date = payload.get("date")
    description = payload.get("description", "")

    if not user_id or not category or amount in (None, "") or not date:
        return jsonify({"error": "Missing expense fields"}), 400

    parsed_date = parse_iso_date(date)
    if not parsed_date:
        return jsonify({"error": "date must use YYYY-MM-DD format"}), 400

    try:
        amount_value = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "amount must be a valid number"}), 400

    if amount_value <= 0:
        return jsonify({"error": "amount must be greater than 0"}), 400

    conn = get_db()
    cursor = conn.cursor()
    budget = cursor.execute("SELECT * FROM budgets WHERE user_id = ?", (user_id,)).fetchone()

    if not budget:
        conn.close()
        return jsonify({"error": "Please set a budget first"}), 400

    cursor.execute(
        "INSERT INTO expenses (budget_id, category, amount, date, description) VALUES (?, ?, ?, ?, ?)",
        (budget["id"], category.strip(), amount_value, date, description.strip()),
    )
    conn.commit()
    expense_id = cursor.lastrowid
    expense = cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()

    # Expense service behavior: call budget service over REST to recalculate budget.
    try:
        recalc_payload = requests.post(
            f"{PUBLIC_FINANCE_URL}/api/budget/recalculate",
            json={"user_id": user_id, "trigger": "expense_added", "expense_id": expense_id},
            timeout=REQUEST_TIMEOUT_SECONDS,
        ).json()
    except requests.RequestException:
        recalc_payload = {"warning": "Budget recalculation unavailable"}

    return jsonify({"expense": row_to_dict(expense), "budget_state": recalc_payload}), 201


@app.post("/api/budget/recalculate")
def recalculate_budget():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db()
    budget, expenses, total_expenses, remaining = compute_budget_snapshot(conn, user_id)
    conn.close()

    if not budget:
        return jsonify({"error": "Budget not found"}), 404

    overspent = remaining < 0
    if overspent:
        send_notification(
            user_id,
            "budget_exceeded",
            "Budget exceeded",
            f"You exceeded your budget by ${abs(remaining):.2f}.",
            severity="critical",
        )

    return jsonify(
        {
            "budget": row_to_dict(budget),
            "total_expenses": total_expenses,
            "remaining": remaining,
            "overspent": overspent,
            "expense_count": len(expenses),
        }
    )


@app.get("/api/summary")
def budget_summary():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db()
    budget, expenses, total_expenses, remaining = compute_budget_snapshot(conn, user_id)
    conn.close()

    return jsonify(
        {
            "has_budget": bool(budget),
            "total_budget": float(budget["total_budget"]) if budget else 0,
            "total_expenses": float(total_expenses),
            "remaining": float(remaining),
            "expense_count": len(expenses),
            "overspent": remaining < 0,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8003")))
