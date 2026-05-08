from flask import Flask, jsonify, request
from requests import RequestException

from microservices.budget_service import _budget_summary
from microservices.common import configure_metrics, db_cursor, json_error
from service_http import request_json


NOTIFICATION_URL_TEMPLATE = "http://notification-service:5007/users/{user_id}/notifications"


def create_app():
    app = Flask(__name__)
    configure_metrics(app)

    @app.get("/health")
    def health():
        return jsonify({"service": "expense", "status": "ok"})

    @app.get("/users/<int:user_id>/expenses")
    def list_expenses(user_id):
        conn, cursor = db_cursor()
        summary = _budget_summary(cursor, user_id)
        conn.close()
        return jsonify(summary["expenses"])

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
        budget = cursor.execute("SELECT * FROM budgets WHERE user_id = ?", (user_id,)).fetchone()
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

        if summary["total_expenses"] > budget["total_budget"]:
            try:
                request_json(
                    "POST",
                    NOTIFICATION_URL_TEMPLATE.format(user_id=user_id),
                    json={
                        "level": "warning",
                        "title": "Expense spike detected",
                        "message": "Recent expenses pushed the trip over the saved budget.",
                    },
                )
            except RequestException:
                pass

        response = jsonify(summary)
        response.status_code = 201
        return response

    return app
