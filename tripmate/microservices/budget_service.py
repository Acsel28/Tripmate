from flask import Flask, jsonify, request
from requests import RequestException

from microservices.common import configure_metrics, db_cursor, dict_from_row, json_error, rows_to_dicts
from service_http import request_json


NOTIFICATION_URL_TEMPLATE = "http://notification-service:5007/users/{user_id}/notifications"


def _budget_summary(cursor, user_id):
    budget = cursor.execute(
        "SELECT * FROM budgets WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    expenses = []
    total_expenses = 0
    remaining = 0

    if budget:
        expenses = cursor.execute(
            "SELECT * FROM expenses WHERE budget_id = ? ORDER BY date DESC",
            (budget["id"],),
        ).fetchall()
        expense_total = cursor.execute(
            "SELECT SUM(amount) AS total FROM expenses WHERE budget_id = ?",
            (budget["id"],),
        ).fetchone()
        total_expenses = expense_total["total"] if expense_total["total"] else 0
        remaining = budget["total_budget"] - total_expenses

    return {
        "budget": dict_from_row(budget),
        "expenses": rows_to_dicts(expenses),
        "total_expenses": total_expenses,
        "remaining": remaining,
    }


def create_app():
    app = Flask(__name__)
    configure_metrics(app)

    @app.get("/health")
    def health():
        return jsonify({"service": "budget", "status": "ok"})

    @app.get("/users/<int:user_id>/budget")
    def get_budget(user_id):
        conn, cursor = db_cursor()
        summary = _budget_summary(cursor, user_id)
        conn.close()
        return jsonify(summary)

    @app.post("/users/<int:user_id>/budget")
    def set_budget(user_id):
        payload = request.get_json(silent=True) or {}
        total_budget = payload.get("total_budget")
        if total_budget is None:
            return json_error("Total budget is required.", 400)

        conn, cursor = db_cursor()
        existing = cursor.execute(
            "SELECT * FROM budgets WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if existing:
            cursor.execute(
                "UPDATE budgets SET total_budget = ? WHERE user_id = ?",
                (float(total_budget), user_id),
            )
        else:
            cursor.execute(
                "INSERT INTO budgets (user_id, total_budget) VALUES (?, ?)",
                (user_id, float(total_budget)),
            )

        conn.commit()
        summary = _budget_summary(cursor, user_id)
        conn.close()
        return jsonify(summary)

    @app.post("/users/<int:user_id>/expenses")
    def add_expense(user_id):
        payload = request.get_json(silent=True) or {}
        category = payload.get("category", "").strip()
        date = payload.get("date", "").strip()
        description = payload.get("description", "").strip()
        amount = payload.get("amount")

        if not category or not date or amount is None:
            return json_error("Category, amount, and date are required.", 400)

        conn, cursor = db_cursor()
        budget = cursor.execute(
            "SELECT * FROM budgets WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if not budget:
            conn.close()
            return json_error("Please set a budget first.", 400)

        cursor.execute(
            """
            INSERT INTO expenses (budget_id, category, amount, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (budget["id"], category, float(amount), date, description),
        )
        conn.commit()
        summary = _budget_summary(cursor, user_id)
        conn.close()

        response = jsonify(summary)
        response.status_code = 201

        budget_data = summary.get("budget")
        if budget_data and summary["total_expenses"] > budget_data["total_budget"]:
            try:
                request_json(
                    "POST",
                    NOTIFICATION_URL_TEMPLATE.format(user_id=user_id),
                    json={
                        "level": "warning",
                        "title": "Budget exceeded",
                        "message": "Your recorded expenses are now above the configured travel budget.",
                    },
                )
            except RequestException:
                pass

        return response

    @app.get("/users/<int:user_id>/assessment")
    def assess_budget(user_id):
        planned_cost = request.args.get("planned_cost", type=float)
        if planned_cost is None:
            return json_error("Planned cost is required.", 400)

        conn, cursor = db_cursor()
        summary = _budget_summary(cursor, user_id)
        conn.close()
        total_budget = summary["budget"]["total_budget"] if summary["budget"] else 0
        total_used = summary["total_expenses"] + planned_cost
        return jsonify(
            {
                "budget": summary["budget"],
                "planned_cost": planned_cost,
                "total_used": total_used,
                "affordable": total_used <= total_budget if summary["budget"] else False,
            }
        )

    return app
