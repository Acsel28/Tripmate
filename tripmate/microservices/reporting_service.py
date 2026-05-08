from flask import Flask, jsonify

from microservices.common import configure_metrics, db_cursor, dict_from_row, rows_to_dicts


def create_app():
    app = Flask(__name__)
    configure_metrics(app)

    @app.get("/health")
    def health():
        return jsonify({"service": "reporting", "status": "ok"})

    @app.get("/users/<int:user_id>/report")
    def report(user_id):
        conn, cursor = db_cursor()

        itineraries = cursor.execute(
            "SELECT * FROM itineraries WHERE user_id = ?",
            (user_id,),
        ).fetchall()

        itinerary_data = []
        for itinerary in itineraries:
            destinations = cursor.execute(
                "SELECT * FROM destinations WHERE itinerary_id = ?",
                (itinerary["id"],),
            ).fetchall()
            itinerary_data.append(
                {
                    "itinerary": dict_from_row(itinerary),
                    "destinations": rows_to_dicts(destinations),
                }
            )

        bookings = cursor.execute(
            "SELECT * FROM bookings WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        total_booking_cost = sum(booking["price"] for booking in bookings)

        budget = cursor.execute(
            "SELECT * FROM budgets WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        expenses = []
        total_expenses = 0
        remaining = 0

        if budget:
            expenses = cursor.execute(
                "SELECT * FROM expenses WHERE budget_id = ?",
                (budget["id"],),
            ).fetchall()
            total = cursor.execute(
                "SELECT SUM(amount) AS total FROM expenses WHERE budget_id = ?",
                (budget["id"],),
            ).fetchone()
            total_expenses = total["total"] if total["total"] else 0
            remaining = budget["total_budget"] - total_expenses

        conn.close()

        return jsonify(
            {
                "itinerary_data": itinerary_data,
                "bookings": rows_to_dicts(bookings),
                "total_booking_cost": total_booking_cost,
                "budget": dict_from_row(budget),
                "expenses": rows_to_dicts(expenses),
                "total_expenses": total_expenses,
                "remaining": remaining,
            }
        )

    return app
