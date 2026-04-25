import os
from datetime import datetime

import requests
from flask import Flask, jsonify, redirect, request

from db import get_db
from gateway_routes import auth as auth_routes, booking as booking_routes, itinerary as itinerary_routes

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = os.environ.get("TRIPMATE_SECRET_KEY", "tripmate-secret-key-change-in-production")

PUBLIC_GATEWAY_URL = os.environ.get("PUBLIC_GATEWAY_URL", "http://localhost:8000")
PUBLIC_AUTH_URL = os.environ.get("PUBLIC_AUTH_URL", "http://localhost:8001")
PUBLIC_TRAVEL_URL = os.environ.get("PUBLIC_TRAVEL_URL", "http://localhost:8002")
PUBLIC_FINANCE_URL = os.environ.get("PUBLIC_FINANCE_URL", "http://localhost:8003")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:8004")
REQUEST_TIMEOUT_SECONDS = float(os.environ.get("INTERNAL_API_TIMEOUT_SECONDS", "5"))

app.register_blueprint(auth_routes.bp)
app.register_blueprint(itinerary_routes.bp)
app.register_blueprint(booking_routes.bp)


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
    return redirect("/itinerary/")


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
        # Notifications are non-blocking in this demo architecture.
        pass


def set_booking_status(cursor, booking_id, new_status):
    allowed_transitions = {
        "pending": {"confirmed", "cancelled"},
        "confirmed": {"cancelled"},
        "cancelled": set(),
    }

    booking = cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if not booking:
        return None, "Booking not found"

    current_status = booking["status"]
    if current_status == new_status:
        return booking, None

    if new_status not in allowed_transitions.get(current_status, set()):
        return None, f"Invalid status transition from {current_status} to {new_status}"

    cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", (new_status, booking_id))
    cursor.execute(
        "INSERT INTO booking_status_history (booking_id, from_status, to_status) VALUES (?, ?, ?)",
        (booking_id, current_status, new_status),
    )
    updated = cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    return updated, None


def generate_recommendations(location):
    normalized = location.lower()
    if any(token in normalized for token in ("paris", "france")):
        return ["Louvre Museum", "Seine Cruise", "Montmartre Walking Tour"]
    if any(token in normalized for token in ("tokyo", "japan")):
        return ["Shibuya Crossing", "Asakusa Temple", "Day trip to Hakone"]
    if any(token in normalized for token in ("new york", "nyc", "usa")):
        return ["Central Park", "Broadway Show", "Brooklyn food tour"]
    return ["Local food tour", "Top-rated walking tour", "City museum pass"]


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "travel"})


@app.get("/api/itineraries")
def list_itineraries():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db()
    itineraries = conn.execute(
        "SELECT * FROM itineraries WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()

    return jsonify({"itineraries": [dict(row) for row in itineraries], "total_trips": len(itineraries)})


@app.post("/api/itineraries")
def create_itinerary():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    title = (payload.get("title") or "").strip()
    start_date_raw = payload.get("start_date")
    end_date_raw = payload.get("end_date")

    if not user_id or not title or not start_date_raw or not end_date_raw:
        return jsonify({"error": "user_id, title, start_date and end_date are required"}), 400

    start_date = parse_iso_date(start_date_raw)
    end_date = parse_iso_date(end_date_raw)
    if not start_date or not end_date:
        return jsonify({"error": "Dates must use YYYY-MM-DD format"}), 400
    if end_date < start_date:
        return jsonify({"error": "end_date must be after or equal to start_date"}), 400

    conn = get_db()
    cursor = conn.cursor()
    overlapping = cursor.execute(
        """
        SELECT 1
        FROM itineraries
        WHERE user_id = ?
          AND start_date IS NOT NULL
          AND end_date IS NOT NULL
          AND NOT (end_date < ? OR start_date > ?)
        LIMIT 1
        """,
        (user_id, start_date_raw, end_date_raw),
    ).fetchone()

    if overlapping:
        conn.close()
        return jsonify({"error": "Trip dates overlap with an existing itinerary"}), 409

    cursor.execute(
        "INSERT INTO itineraries (user_id, title, start_date, end_date) VALUES (?, ?, ?, ?)",
        (user_id, title, start_date_raw, end_date_raw),
    )
    conn.commit()
    itinerary_id = cursor.lastrowid
    itinerary = conn.execute("SELECT * FROM itineraries WHERE id = ?", (itinerary_id,)).fetchone()
    conn.close()

    return jsonify({"itinerary": row_to_dict(itinerary)}), 201


@app.get("/api/itineraries/<int:itinerary_id>")
def get_itinerary_detail(itinerary_id):
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db()
    itinerary = conn.execute(
        "SELECT * FROM itineraries WHERE id = ? AND user_id = ?", (itinerary_id, user_id)
    ).fetchone()
    if not itinerary:
        conn.close()
        return jsonify({"error": "Itinerary not found"}), 404

    destinations = conn.execute(
        "SELECT * FROM destinations WHERE itinerary_id = ? ORDER BY date", (itinerary_id,)
    ).fetchall()
    conn.close()

    return jsonify(
        {
            "itinerary": row_to_dict(itinerary),
            "destinations": [dict(row) for row in destinations],
        }
    )


@app.post("/api/itineraries/<int:itinerary_id>/destinations")
def add_destination(itinerary_id):
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    location = (payload.get("location") or "").strip()
    date_raw = payload.get("date")
    notes = payload.get("notes", "")

    if not user_id or not location or not date_raw:
        return jsonify({"error": "user_id, location and date are required"}), 400

    destination_date = parse_iso_date(date_raw)
    if not destination_date:
        return jsonify({"error": "date must use YYYY-MM-DD format"}), 400

    conn = get_db()
    cursor = conn.cursor()

    itinerary = cursor.execute(
        "SELECT * FROM itineraries WHERE id = ? AND user_id = ?", (itinerary_id, user_id)
    ).fetchone()
    if not itinerary:
        conn.close()
        return jsonify({"error": "Itinerary not found"}), 404

    itinerary_start = parse_iso_date(itinerary["start_date"]) if itinerary["start_date"] else None
    itinerary_end = parse_iso_date(itinerary["end_date"]) if itinerary["end_date"] else None
    if itinerary_start and itinerary_end and not (itinerary_start <= destination_date <= itinerary_end):
        conn.close()
        return jsonify({"error": "Destination date must be within itinerary date range"}), 400

    cursor.execute(
        "INSERT INTO destinations (itinerary_id, location, date, notes) VALUES (?, ?, ?, ?)",
        (itinerary_id, location, date_raw, notes),
    )
    conn.commit()
    destination_id = cursor.lastrowid
    destination = conn.execute("SELECT * FROM destinations WHERE id = ?", (destination_id,)).fetchone()
    recommendations = generate_recommendations(location)
    send_notification(
        user_id,
        "trip_recommendations_generated",
        "New trip recommendations available",
        f"Added {location}. Suggested activities: {', '.join(recommendations)}",
        severity="info",
    )

    conn.close()

    return jsonify({"destination": row_to_dict(destination), "recommendations": recommendations}), 201


@app.delete("/api/destinations/<int:destination_id>")
def delete_destination(destination_id):
    conn = get_db()
    destination = conn.execute("SELECT * FROM destinations WHERE id = ?", (destination_id,)).fetchone()

    if not destination:
        conn.close()
        return jsonify({"error": "Destination not found"}), 404

    itinerary_id = destination["itinerary_id"]
    conn.execute("DELETE FROM destinations WHERE id = ?", (destination_id,))
    conn.commit()
    conn.close()

    return jsonify({"deleted": True, "itinerary_id": itinerary_id})


@app.get("/api/bookings")
def list_bookings():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db()
    bookings = conn.execute(
        "SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()

    total_trip_cost = sum(row["price"] for row in bookings if row["status"] == "confirmed")
    return jsonify({"bookings": [dict(row) for row in bookings], "total_trip_cost": total_trip_cost})


@app.post("/api/bookings")
def create_booking():
    payload = request.get_json(silent=True) or {}

    required_fields = ("user_id", "item_type", "item_name", "date", "price")
    if not all(field in payload and payload[field] not in (None, "") for field in required_fields):
        return jsonify({"error": "Missing booking fields"}), 400

    item_type = str(payload["item_type"]).strip().lower()
    if item_type not in {"flight", "hotel"}:
        return jsonify({"error": "item_type must be flight or hotel"}), 400

    booking_date = parse_iso_date(payload["date"])
    if not booking_date:
        return jsonify({"error": "date must use YYYY-MM-DD format"}), 400

    try:
        price = float(payload["price"])
    except (TypeError, ValueError):
        return jsonify({"error": "price must be a valid number"}), 400

    if price <= 0:
        return jsonify({"error": "price must be greater than 0"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bookings (user_id, item_type, item_name, date, price, status) VALUES (?, ?, ?, ?, ?, ?)",
        (
            payload["user_id"],
            item_type,
            payload["item_name"],
            payload["date"],
            price,
            "pending",
        ),
    )
    conn.commit()
    booking_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO booking_status_history (booking_id, from_status, to_status) VALUES (?, ?, ?)",
        (booking_id, None, "pending"),
    )

    booking, transition_error = set_booking_status(cursor, booking_id, "confirmed")
    if transition_error:
        conn.rollback()
        conn.close()
        return jsonify({"error": transition_error}), 400

    conn.commit()
    conn.close()

    send_notification(
        payload["user_id"],
        "booking_confirmed",
        "Booking confirmed",
        f"Your {item_type} booking for {payload['item_name']} on {payload['date']} is confirmed.",
        severity="success",
    )

    return jsonify({"booking": row_to_dict(booking)}), 201


@app.patch("/api/bookings/<int:booking_id>/status")
def update_booking_status(booking_id):
    payload = request.get_json(silent=True) or {}
    new_status = (payload.get("status") or "").strip().lower()

    if new_status not in {"pending", "confirmed", "cancelled"}:
        return jsonify({"error": "status must be pending, confirmed or cancelled"}), 400

    conn = get_db()
    cursor = conn.cursor()
    booking, transition_error = set_booking_status(cursor, booking_id, new_status)
    if transition_error:
        conn.close()
        return jsonify({"error": transition_error}), 400

    conn.commit()
    conn.close()

    if new_status == "cancelled":
        send_notification(
            booking["user_id"],
            "booking_cancelled",
            "Booking cancelled",
            f"Your booking for {booking['item_name']} was cancelled.",
            severity="warning",
        )

    return jsonify({"booking": row_to_dict(booking)}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8002")))
