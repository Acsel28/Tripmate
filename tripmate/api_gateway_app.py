import os

from flask import Flask, jsonify, request
from requests import RequestException

from microservices.common import configure_metrics
from service_client import get_json, post_json


app = Flask(__name__)
app.secret_key = os.environ.get("TRIPMATE_SECRET_KEY", "tripmate-secret-key-change-in-production")
configure_metrics(app)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/<path:_path>", methods=["OPTIONS"])
def preflight(_path):
    return ("", 204)


@app.get("/health")
def health():
    return jsonify({"service": "api-gateway", "status": "ok"})


@app.post("/api/auth/register")
def register():
    return jsonify(post_json("auth", "/register", request.get_json(silent=True) or {})), 201


@app.post("/api/auth/login")
def login():
    return jsonify(post_json("auth", "/login", request.get_json(silent=True) or {}))


@app.get("/api/users/<int:user_id>/dashboard")
def dashboard(user_id):
    try:
        return jsonify(
            {
                "trips": get_json("trip", f"/users/{user_id}/trips"),
                "notifications": get_json("notification", f"/users/{user_id}/notifications"),
                "budget": get_json("budget", f"/users/{user_id}/budget"),
                "report": get_json("reporting", f"/users/{user_id}/report"),
            }
        )
    except RequestException:
        return jsonify({"error": "One or more backend services are unavailable."}), 503


@app.post("/api/users/<int:user_id>/trips")
def create_trip(user_id):
    try:
        return jsonify(post_json("trip", f"/users/{user_id}/trips", request.get_json(silent=True) or {})), 201
    except RequestException as exc:
        response = getattr(exc, "response", None)
        if response is not None:
            return jsonify(response.json()), response.status_code
        return jsonify({"error": "Trip service is unavailable."}), 503


@app.post("/api/users/<int:user_id>/plan")
def create_plan(user_id):
    try:
        return jsonify(post_json("planning", f"/users/{user_id}/plan", request.get_json(silent=True) or {}))
    except RequestException as exc:
        response = getattr(exc, "response", None)
        if response is not None:
            return jsonify(response.json()), response.status_code
        return jsonify({"error": "Planning service is unavailable."}), 503


@app.get("/api/users/<int:user_id>/notifications")
def notifications(user_id):
    return jsonify(get_json("notification", f"/users/{user_id}/notifications"))


@app.post("/api/users/<int:user_id>/budget")
def set_budget(user_id):
    return jsonify(post_json("budget", f"/users/{user_id}/budget", request.get_json(silent=True) or {}))


@app.post("/api/users/<int:user_id>/expenses")
def add_expense(user_id):
    return jsonify(post_json("expense", f"/users/{user_id}/expenses", request.get_json(silent=True) or {})), 201


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )
