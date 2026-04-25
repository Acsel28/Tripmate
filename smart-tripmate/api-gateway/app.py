import os

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

AUTH = os.environ.get("AUTH_SERVICE_URL", "http://auth-service:5001")
TRIP = os.environ.get("TRIP_SERVICE_URL", "http://trip-service:5003")
PLAN = os.environ.get("PLANNING_SERVICE_URL", "http://planning-service:5004")
BUDGET = os.environ.get("BUDGET_SERVICE_URL", "http://budget-service:5007")
NOTIFY = os.environ.get("NOTIFICATION_SERVICE_URL", "http://notification-service:5008")


def proxy(method, url, **kwargs):
    try:
        response = requests.request(method, url, timeout=8, **kwargs)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as exc:
        return jsonify({"error": str(exc)}), 503
    except ValueError:
        return jsonify({"error": "invalid upstream response"}), 502


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "api-gateway"})


@app.post("/auth/register")
def register():
    return proxy("POST", f"{AUTH}/register", json=request.get_json(silent=True) or {})


@app.post("/auth/login")
def login():
    return proxy("POST", f"{AUTH}/login", json=request.get_json(silent=True) or {})


@app.post("/trips")
def create_trip():
    payload = request.get_json(silent=True) or {}
    return proxy("POST", f"{TRIP}/trips", json=payload)


@app.get("/trips")
def list_trips():
    return proxy("GET", f"{TRIP}/trips", params=request.args)


@app.post("/plan")
def plan():
    return proxy("POST", f"{PLAN}/plan", json=request.get_json(silent=True) or {})


@app.post("/budgets")
def set_budget():
    return proxy("POST", f"{BUDGET}/budgets", json=request.get_json(silent=True) or {})


@app.get("/notifications")
def notifications():
    return proxy("GET", f"{NOTIFY}/notifications", params=request.args)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
