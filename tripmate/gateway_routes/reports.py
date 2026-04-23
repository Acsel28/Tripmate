from functools import wraps

from flask import Blueprint, flash, redirect, render_template, session, url_for

from gateway_routes.client import ServiceError, finance_get, travel_get

bp = Blueprint("reports", __name__, url_prefix="/reports")


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


@bp.route("/")
@login_required
def index():
    user_id = session["user_id"]

    try:
        itineraries_payload = travel_get("/api/itineraries", params={"user_id": user_id})
        itineraries = itineraries_payload.get("itineraries", [])

        itinerary_data = []
        for itinerary in itineraries:
            detail_payload = travel_get(f"/api/itineraries/{itinerary['id']}", params={"user_id": user_id})
            itinerary_data.append(
                {
                    "itinerary": AttrDict(detail_payload["itinerary"]),
                    "destinations": to_attr_list(detail_payload.get("destinations", [])),
                }
            )

        bookings_payload = travel_get("/api/bookings", params={"user_id": user_id})
        bookings = to_attr_list(bookings_payload.get("bookings", []))
        total_booking_cost = sum([booking.price for booking in bookings])

        budget_payload = finance_get("/api/budget", params={"user_id": user_id})
        budget = AttrDict(budget_payload["budget"]) if budget_payload.get("budget") else None
        expenses = to_attr_list(budget_payload.get("expenses", []))
        total_expenses = budget_payload.get("total_expenses", 0)
        remaining = budget_payload.get("remaining", 0)
    except ServiceError as exc:
        flash(str(exc))
        return redirect(url_for("dashboard"))

    return render_template(
        "report.html",
        itinerary_data=itinerary_data,
        bookings=bookings,
        total_booking_cost=total_booking_cost,
        budget=budget,
        expenses=expenses,
        total_expenses=total_expenses,
        remaining=remaining,
    )
