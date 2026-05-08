import json

from flask import Flask, jsonify, request
from requests import RequestException

from microservices.common import configure_metrics, db_cursor, dict_from_row, json_error, rows_to_dicts
from planning_engine import PlanningError, parse_trip_dates
from service_http import request_json


def create_app():
    app = Flask(__name__)
    configure_metrics(app)

    recommendation_url = "http://recommendation-service:5008/recommendations"

    @app.get("/health")
    def health():
        return jsonify({"service": "trip", "status": "ok"})

    @app.get("/users/<int:user_id>/trips")
    def list_trips(user_id):
        conn, cursor = db_cursor()
        rows = cursor.execute(
            "SELECT * FROM trips WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        conn.close()
        return jsonify(rows_to_dicts(rows))

    @app.post("/users/<int:user_id>/trips")
    def create_trip(user_id):
        payload = request.get_json(silent=True) or {}
        required = [
            "source_city",
            "destination_city",
            "start_date",
            "end_date",
            "budget",
        ]
        if any(not payload.get(field) for field in required):
            return json_error("Source, destination, dates, and budget are required.", 400)

        try:
            parse_trip_dates(payload["start_date"], payload["end_date"])
        except PlanningError as exc:
            return json_error(str(exc), 400)

        preferences = payload.get("preferences", {})
        conn, cursor = db_cursor()
        cursor.execute(
            """
            INSERT INTO trips (
                user_id, source_city, destination_city, start_date, end_date,
                traveler_count, budget, preferences, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                payload["source_city"].strip(),
                payload["destination_city"].strip(),
                payload["start_date"],
                payload["end_date"],
                int(payload.get("traveler_count", 1)),
                float(payload["budget"]),
                json.dumps(preferences),
                "planned",
            ),
        )
        trip_id = cursor.lastrowid
        conn.commit()
        trip = cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
        conn.close()

        recommendations = []
        try:
            recommendation_payload = dict(payload)
            recommendations = request_json("POST", recommendation_url, json=recommendation_payload)["recommendations"]
        except RequestException:
            recommendations = []

        response = jsonify({"trip": dict_from_row(trip), "recommendations": recommendations})
        response.status_code = 201
        return response

    return app
