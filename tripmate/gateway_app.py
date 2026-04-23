import os
from functools import wraps

from flask import Flask, redirect, render_template, session, url_for

from gateway_routes.client import ServiceError, finance_get, travel_get
from gateway_routes import auth, itinerary, booking, budget, reports

app = Flask(__name__)
app.secret_key = os.environ.get("TRIPMATE_SECRET_KEY", "tripmate-secret-key-change-in-production")


class AttrDict(dict):
    __getattr__ = dict.get


def to_attr_list(items):
    return [AttrDict(item) for item in items]


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
        budget_payload = finance_get("/api/budget", params={"user_id": user_id})

        itineraries = to_attr_list(itineraries_payload.get("itineraries", []))[:5]
        bookings = to_attr_list(bookings_payload.get("bookings", []))[:5]
        budget_obj = AttrDict(budget_payload["budget"]) if budget_payload.get("budget") else None
        total_expenses = budget_payload.get("total_expenses", 0)
    except ServiceError:
        itineraries = []
        bookings = []
        budget_obj = None
        total_expenses = 0

    return render_template(
        "dashboard.html",
        itineraries=itineraries,
        bookings=bookings,
        budget=budget_obj,
        total_expenses=total_expenses,
        user_name=session.get("user_name"),
    )


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )
