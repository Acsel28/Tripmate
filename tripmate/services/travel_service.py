from flask import Flask, jsonify, request

from db import get_db

app = Flask(__name__)


def row_to_dict(row):
    return dict(row) if row else None


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

    return jsonify({"itineraries": [dict(row) for row in itineraries]})


@app.post("/api/itineraries")
def create_itinerary():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    title = (payload.get("title") or "").strip()

    if not user_id or not title:
        return jsonify({"error": "user_id and title are required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO itineraries (user_id, title) VALUES (?, ?)", (user_id, title))
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
    location = (payload.get("location") or "").strip()
    date = payload.get("date")
    notes = payload.get("notes", "")

    if not location or not date:
        return jsonify({"error": "location and date are required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO destinations (itinerary_id, location, date, notes) VALUES (?, ?, ?, ?)",
        (itinerary_id, location, date, notes),
    )
    conn.commit()
    destination_id = cursor.lastrowid
    destination = conn.execute("SELECT * FROM destinations WHERE id = ?", (destination_id,)).fetchone()
    conn.close()

    return jsonify({"destination": row_to_dict(destination)}), 201


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

    return jsonify({"bookings": [dict(row) for row in bookings]})


@app.post("/api/bookings")
def create_booking():
    payload = request.get_json(silent=True) or {}

    required_fields = ("user_id", "item_type", "item_name", "date", "price")
    if not all(field in payload and payload[field] not in (None, "") for field in required_fields):
        return jsonify({"error": "Missing booking fields"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bookings (user_id, item_type, item_name, date, price, status) VALUES (?, ?, ?, ?, ?, ?)",
        (
            payload["user_id"],
            payload["item_type"],
            payload["item_name"],
            payload["date"],
            float(payload["price"]),
            "confirmed",
        ),
    )
    conn.commit()
    booking_id = cursor.lastrowid
    booking = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    conn.close()

    return jsonify({"booking": row_to_dict(booking)}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002)
