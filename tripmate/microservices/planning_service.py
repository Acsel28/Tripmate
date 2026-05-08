from flask import Flask, jsonify, request
from requests import RequestException

from microservices.common import configure_metrics, db_cursor, json_error
from planning_engine import PlanningError, build_plan_variants, parse_trip_dates, serialize_payload
from service_http import request_json


BOOKING_OPTIONS_URL = "http://booking-service:5003/options"
BUDGET_URL_TEMPLATE = "http://budget-service:5004/users/{user_id}/budget"
NOTIFICATION_URL_TEMPLATE = "http://notification-service:5007/users/{user_id}/notifications"


def create_app():
    app = Flask(__name__)
    configure_metrics(app)

    @app.get("/health")
    def health():
        return jsonify({"service": "planning", "status": "ok"})

    @app.post("/users/<int:user_id>/plan")
    def create_plan(user_id):
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

        payload["traveler_count"] = int(payload.get("traveler_count", 1))
        payload["preferences"] = payload.get("preferences", {})

        try:
            parse_trip_dates(payload["start_date"], payload["end_date"])
            booking_options = request_json("GET", BOOKING_OPTIONS_URL, params=payload)
            plan_bundle = build_plan_variants(payload, booking_options)
        except PlanningError as exc:
            return json_error(str(exc), 400)
        except RequestException:
            return json_error("Booking service is unavailable.", 503)

        try:
            budget_summary = request_json("GET", BUDGET_URL_TEMPLATE.format(user_id=user_id))
        except RequestException:
            budget_summary = {"budget": None, "total_expenses": 0, "remaining": None}

        conn, cursor = db_cursor()
        trip_row = cursor.execute(
            """
            SELECT id FROM trips
            WHERE user_id = ? AND source_city = ? AND destination_city = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (user_id, payload["source_city"], payload["destination_city"]),
        ).fetchone()

        saved_plans = []
        for plan in plan_bundle["plans"].values():
            cursor.execute(
                """
                INSERT INTO travel_plans (user_id, trip_id, plan_type, title, total_cost, affordable, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    trip_row["id"] if trip_row else None,
                    plan["plan_type"],
                    plan["title"],
                    plan["cost_breakdown"]["total_cost"],
                    1 if plan["affordable"] else 0,
                    serialize_payload(plan),
                ),
            )
            saved_plans.append(plan)
        conn.commit()
        conn.close()

        cheapest_plan = plan_bundle["plans"]["cheapest"]
        if not cheapest_plan["affordable"]:
            try:
                request_json(
                    "POST",
                    NOTIFICATION_URL_TEMPLATE.format(user_id=user_id),
                    json={
                        "level": "warning",
                        "title": "Trip exceeds budget",
                        "message": "Your cheapest plan is currently above budget. Review the savings suggestions.",
                    },
                )
            except RequestException:
                pass

        return jsonify(
            {
                "request": payload,
                "budget_summary": budget_summary,
                "plans": saved_plans,
                "cheaper_alternatives": plan_bundle["cheaper_alternatives"],
            }
        )

    return app
