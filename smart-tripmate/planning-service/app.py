import os
from datetime import datetime

import requests
from flask import Flask, jsonify, request

from planner import build_suggestions, generate_plans, parse_dates

app = Flask(__name__)

BOOKING_SERVICE_URL = os.environ.get("BOOKING_SERVICE_URL", "http://booking-service:5005")
BUDGET_SERVICE_URL = os.environ.get("BUDGET_SERVICE_URL", "http://budget-service:5007")
TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "5"))


def fetch_json(url, params=None):
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise RuntimeError(str(exc)) from exc


def validate_payload(payload):
    required = ["source_city", "destination_city", "start_date", "end_date", "budget", "preferences"]
    for field in required:
        if field not in payload:
            raise ValueError(f"{field} is required")

    parse_dates(payload["start_date"], payload["end_date"])

    try:
        budget = float(payload["budget"])
    except (TypeError, ValueError) as exc:
        raise ValueError("budget must be numeric") from exc

    if budget <= 0:
        raise ValueError("budget must be greater than 0")

    return budget


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "planning-service"})


@app.post("/plan")
def plan_trip():
    payload = request.get_json(silent=True) or {}
    try:
        budget = validate_payload(payload)
        start, end = parse_dates(payload["start_date"], payload["end_date"])
        nights = max((end - start).days, 1)

        source = payload["source_city"]
        destination = payload["destination_city"]
        preferences = payload.get("preferences", {})

        options = {
            "flights": fetch_json(f"{BOOKING_SERVICE_URL}/flights", {"from_city": source, "to_city": destination}).get("flights", []),
            "trains": fetch_json(f"{BOOKING_SERVICE_URL}/trains", {"from_city": source, "to_city": destination}).get("trains", []),
            "hotels": fetch_json(
                f"{BOOKING_SERVICE_URL}/hotels",
                {"city": destination, "type": preferences.get("hotel_type")},
            ).get("hotels", []),
            "activities": fetch_json(f"{BOOKING_SERVICE_URL}/activities", {"city": destination}).get("activities", []),
        }

        if (not options["flights"] and not options["trains"]) or not options["hotels"]:
            return jsonify({"error": "No travel/hotel options available for selected route"}), 404

        plans = generate_plans(options, nights, budget, preferences.get("transport_type"))
        if not plans:
            return jsonify({"error": "No feasible plans generated"}), 404

        cheapest = min(plans, key=lambda x: x["total_cost"])
        budget_eval = requests.post(
            f"{BUDGET_SERVICE_URL}/evaluate",
            json={"user_id": payload.get("user_id", "guest"), "budget": budget, "total_cost": cheapest["total_cost"]},
            timeout=TIMEOUT,
        )
        budget_eval.raise_for_status()

        return jsonify(
            {
                "trip_window": {"start_date": payload["start_date"], "end_date": payload["end_date"], "nights": nights},
                "budget": budget,
                "plans": plans,
                "budget_assessment": budget_eval.json(),
                "suggestions": build_suggestions(plans, budget),
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"error": f"booking-service failure: {exc}"}), 503
    except requests.RequestException as exc:
        return jsonify({"error": f"budget-service failure: {exc}"}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004)
