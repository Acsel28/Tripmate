from flask import Flask, jsonify, request

from microservices.common import configure_metrics, db_cursor, dict_from_row, json_error, rows_to_dicts


def create_app():
    app = Flask(__name__)
    configure_metrics(app)

    @app.get("/health")
    def health():
        return jsonify({"service": "itinerary", "status": "ok"})

    @app.get("/users/<int:user_id>/itineraries")
    def list_itineraries(user_id):
        limit = request.args.get("limit", type=int)
        conn, cursor = db_cursor()
        query = "SELECT * FROM itineraries WHERE user_id = ? ORDER BY created_at DESC"
        params = [user_id]
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        itineraries = cursor.execute(query, tuple(params)).fetchall()
        conn.close()
        return jsonify(rows_to_dicts(itineraries))

    @app.post("/users/<int:user_id>/itineraries")
    def create_itinerary(user_id):
        payload = request.get_json(silent=True) or {}
        title = payload.get("title", "").strip()
        if not title:
            return json_error("Title is required.", 400)

        conn, cursor = db_cursor()
        cursor.execute(
            "INSERT INTO itineraries (user_id, title) VALUES (?, ?)",
            (user_id, title),
        )
        itinerary_id = cursor.lastrowid
        conn.commit()
        itinerary = cursor.execute(
            "SELECT * FROM itineraries WHERE id = ?",
            (itinerary_id,),
        ).fetchone()
        conn.close()

        response = jsonify(dict_from_row(itinerary))
        response.status_code = 201
        return response

    @app.get("/users/<int:user_id>/itineraries/<int:itinerary_id>")
    def get_itinerary(user_id, itinerary_id):
        conn, cursor = db_cursor()
        itinerary = cursor.execute(
            "SELECT * FROM itineraries WHERE id = ? AND user_id = ?",
            (itinerary_id, user_id),
        ).fetchone()
        if not itinerary:
            conn.close()
            return json_error("Itinerary not found.", 404)

        destinations = cursor.execute(
            "SELECT * FROM destinations WHERE itinerary_id = ? ORDER BY date",
            (itinerary_id,),
        ).fetchall()
        conn.close()

        return jsonify(
            {
                "itinerary": dict_from_row(itinerary),
                "destinations": rows_to_dicts(destinations),
            }
        )

    @app.post("/users/<int:user_id>/itineraries/<int:itinerary_id>/destinations")
    def add_destination(user_id, itinerary_id):
        payload = request.get_json(silent=True) or {}
        location = payload.get("location", "").strip()
        date = payload.get("date", "").strip()
        notes = payload.get("notes", "").strip()
        if not location or not date:
            return json_error("Location and date are required.", 400)

        conn, cursor = db_cursor()
        itinerary = cursor.execute(
            "SELECT * FROM itineraries WHERE id = ? AND user_id = ?",
            (itinerary_id, user_id),
        ).fetchone()
        if not itinerary:
            conn.close()
            return json_error("Itinerary not found.", 404)

        cursor.execute(
            "INSERT INTO destinations (itinerary_id, location, date, notes) VALUES (?, ?, ?, ?)",
            (itinerary_id, location, date, notes),
        )
        destination_id = cursor.lastrowid
        conn.commit()
        destination = cursor.execute(
            "SELECT * FROM destinations WHERE id = ?",
            (destination_id,),
        ).fetchone()
        conn.close()

        response = jsonify(dict_from_row(destination))
        response.status_code = 201
        return response

    @app.delete("/users/<int:user_id>/destinations/<int:destination_id>")
    def delete_destination(user_id, destination_id):
        conn, cursor = db_cursor()
        destination = cursor.execute(
            """
            SELECT d.*, i.user_id
            FROM destinations d
            JOIN itineraries i ON i.id = d.itinerary_id
            WHERE d.id = ? AND i.user_id = ?
            """,
            (destination_id, user_id),
        ).fetchone()
        if not destination:
            conn.close()
            return json_error("Destination not found.", 404)

        cursor.execute("DELETE FROM destinations WHERE id = ?", (destination_id,))
        conn.commit()
        conn.close()
        return jsonify({"deleted": True, "destination_id": destination_id})

    return app
