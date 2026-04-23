from flask import Flask, jsonify, request

from db import get_db

app = Flask(__name__)


def row_to_dict(row):
    return dict(row) if row else None


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "finance"})


@app.get("/api/budget")
def get_budget():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db()
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
        remaining = budget["total_budget"] - total_expenses

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

    conn = get_db()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT * FROM budgets WHERE user_id = ?", (user_id,)).fetchone()

    if existing:
        cursor.execute("UPDATE budgets SET total_budget = ? WHERE user_id = ?", (float(total_budget), user_id))
    else:
        cursor.execute("INSERT INTO budgets (user_id, total_budget) VALUES (?, ?)", (user_id, float(total_budget)))

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

    conn = get_db()
    cursor = conn.cursor()
    budget = cursor.execute("SELECT * FROM budgets WHERE user_id = ?", (user_id,)).fetchone()

    if not budget:
        conn.close()
        return jsonify({"error": "Please set a budget first"}), 400

    cursor.execute(
        "INSERT INTO expenses (budget_id, category, amount, date, description) VALUES (?, ?, ?, ?, ?)",
        (budget["id"], category, float(amount), date, description),
    )
    conn.commit()
    expense_id = cursor.lastrowid
    expense = cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()

    return jsonify({"expense": row_to_dict(expense)}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003)
