import os
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, session, url_for

from gateway_routes.client import ServiceError, finance_get, notification_get, travel_get
from gateway_routes import auth, itinerary, booking, budget, reports

app = Flask(__name__)
app.secret_key = os.environ.get("TRIPMATE_SECRET_KEY", "tripmate-secret-key-change-in-production")

PUBLIC_GATEWAY_URL = os.environ.get("PUBLIC_GATEWAY_URL", "http://localhost:8000")
PUBLIC_AUTH_URL = os.environ.get("PUBLIC_AUTH_URL", "http://localhost:8001")
PUBLIC_TRAVEL_URL = os.environ.get("PUBLIC_TRAVEL_URL", "http://localhost:8002")
PUBLIC_FINANCE_URL = os.environ.get("PUBLIC_FINANCE_URL", "http://localhost:8003")
PUBLIC_NOTIFICATION_URL = os.environ.get("PUBLIC_NOTIFICATION_URL", "http://localhost:8004")


class AttrDict(dict):
    __getattr__ = dict.get


def to_attr_list(items):
    return [AttrDict(item) for item in items]


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
            "notifications": f"{PUBLIC_NOTIFICATION_URL}/api/notifications",
        }
    }


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


app.register_blueprint(auth.bp)
app.register_blueprint(itinerary.bp)
app.register_blueprint(booking.bp)
app.register_blueprint(budget.bp)
app.register_blueprint(reports.bp)


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("auth.login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]

    try:
        itineraries_payload = travel_get("/api/itineraries", params={"user_id": user_id})
        bookings_payload = travel_get("/api/bookings", params={"user_id": user_id})
        budget_payload = finance_get("/api/summary", params={"user_id": user_id})
        notifications_payload = notification_get("/api/notifications", params={"user_id": user_id, "limit": 8})

        itineraries = to_attr_list(itineraries_payload.get("itineraries", []))[:5]
        bookings = to_attr_list(bookings_payload.get("bookings", []))[:5]
        notifications = to_attr_list(notifications_payload.get("notifications", []))
        total_trips = itineraries_payload.get("total_trips", len(itineraries_payload.get("itineraries", [])))
        total_expenses = budget_payload.get("total_expenses", 0)
        remaining_budget = budget_payload.get("remaining", 0)
        total_trip_cost = bookings_payload.get("total_trip_cost", 0)
        has_budget = budget_payload.get("has_budget", False)
    except ServiceError:
        itineraries = []
        bookings = []
        notifications = []
        total_trips = 0
        total_expenses = 0
        remaining_budget = 0
        total_trip_cost = 0
        has_budget = False

    return render_template(
        "dashboard.html",
        itineraries=itineraries,
        bookings=bookings,
        notifications=notifications,
        total_trips=total_trips,
        total_expenses=total_expenses,
        remaining_budget=remaining_budget,
        total_trip_cost=total_trip_cost,
        has_budget=has_budget,
        user_name=session.get("user_name"),
    )


@app.get("/api/dashboard/summary")
@login_required
def dashboard_summary():
    user_id = session["user_id"]

    try:
        itineraries_payload = travel_get("/api/itineraries", params={"user_id": user_id})
        bookings_payload = travel_get("/api/bookings", params={"user_id": user_id})
        budget_payload = finance_get("/api/summary", params={"user_id": user_id})
        notifications_payload = notification_get("/api/notifications", params={"user_id": user_id, "limit": 8})
    except ServiceError as exc:
        return jsonify({"error": str(exc)}), 503

    return jsonify(
        {
            "metrics": {
                "total_trips": itineraries_payload.get("total_trips", 0),
                "total_trip_cost": bookings_payload.get("total_trip_cost", 0),
                "total_expenses": budget_payload.get("total_expenses", 0),
                "remaining_budget": budget_payload.get("remaining", 0),
                "has_budget": budget_payload.get("has_budget", False),
            },
            "notifications": notifications_payload.get("notifications", []),
        }
    )


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )
