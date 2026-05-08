from flask import Flask, jsonify, request

from catalog import build_booking_catalog
from microservices.common import configure_metrics, dict_from_row, rows_to_dicts, json_error, db_cursor
from planning_engine import PlanningError


DUMMY_FLIGHTS = [
    {"name": "Air France AF123", "price": 450.00, "departure": "08:00", "arrival": "12:00"},
    {"name": "Lufthansa LH456", "price": 520.00, "departure": "10:30", "arrival": "14:30"},
    {"name": "British Airways BA789", "price": 480.00, "departure": "14:00", "arrival": "18:00"},
]

DUMMY_HOTELS = [
    {"name": "Grand Hotel Paris", "price": 180.00, "rating": 4.5},
    {"name": "Cozy Inn", "price": 120.00, "rating": 4.0},
    {"name": "Luxury Resort", "price": 350.00, "rating": 5.0},
]


def create_app():
    app = Flask(__name__)
    configure_metrics(app)

    @app.get("/health")
    def health():
        return jsonify({"service": "booking", "status": "ok"})

    @app.get("/catalog")
    def catalog():
        return jsonify({"flights": DUMMY_FLIGHTS, "hotels": DUMMY_HOTELS})

    @app.get("/options")
    def options():
        source_city = request.args.get("source_city", "").strip()
        destination_city = request.args.get("destination_city", "").strip()
        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()
        traveler_count = request.args.get("traveler_count", default=1, type=int)

        if not source_city or not destination_city or not start_date or not end_date:
            return json_error("Source, destination, and dates are required.", 400)

        try:
            return jsonify(
                build_booking_catalog(
                    source_city=source_city,
                    destination_city=destination_city,
                    start_date=start_date,
                    end_date=end_date,
                    traveler_count=traveler_count,
                )
            )
        except PlanningError as exc:
            return json_error(str(exc), 400)

    @app.get("/users/<int:user_id>/bookings")
    def list_bookings(user_id):
        limit = request.args.get("limit", type=int)
        conn, cursor = db_cursor()
        query = "SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC"
        params = [user_id]
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        bookings = cursor.execute(query, tuple(params)).fetchall()
        conn.close()
        return jsonify(rows_to_dicts(bookings))

    @app.post("/users/<int:user_id>/bookings")
    def create_booking(user_id):
        payload = request.get_json(silent=True) or {}
        item_type = payload.get("item_type", "").strip()
        item_name = payload.get("item_name", "").strip()
        date = payload.get("date", "").strip()
        price = payload.get("price")

        if not item_type or not item_name or not date or price is None:
            return json_error("Item type, item name, date, and price are required.", 400)

        conn, cursor = db_cursor()
        cursor.execute(
            """
            INSERT INTO bookings (user_id, item_type, item_name, date, price, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, item_type, item_name, date, float(price), "confirmed"),
        )
        booking_id = cursor.lastrowid
        conn.commit()
        booking = cursor.execute(
            "SELECT * FROM bookings WHERE id = ?",
            (booking_id,),
        ).fetchone()
        conn.close()

        response = jsonify(dict_from_row(booking))
        response.status_code = 201
        return response

    return app
