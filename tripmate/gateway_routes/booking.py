from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from gateway_routes.client import ServiceError, travel_get, travel_post

bp = Blueprint("booking", __name__, url_prefix="/booking")

DUMMY_FLIGHTS = [
    {"name": "Air France AF123", "price": 450.00, "departure": "08:00", "arrival": "12:00"},
    {"name": "Lufthansa LH456", "price": 520.00, "departure": "10:30", "arrival": "14:30"},
    {"name": "British Airways BA789", "price": 480.00, "departure": "14:00", "arrival": "18:00"},
]

DUMMY_HOTELS = [
    {"name": "Grand Hotel Paris", "price": 180.00, "rating": 4.5},
    {"name": "Cozy Inn", "price": 120.00, "rating": 4.0},
    {"name": "Luxury Resort", "price": 350.00, "rating": 5.0},
]


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
    try:
        payload = travel_get("/api/bookings", params={"user_id": session["user_id"]})
        bookings = to_attr_list(payload.get("bookings", []))
    except ServiceError as exc:
        flash(str(exc))
        bookings = []

    return render_template("booking.html", bookings=bookings, flights=DUMMY_FLIGHTS, hotels=DUMMY_HOTELS)


@bp.route("/book", methods=["POST"])
@login_required
def book():
    try:
        travel_post(
            "/api/bookings",
            {
                "user_id": session["user_id"],
                "item_type": request.form["item_type"],
                "item_name": request.form["item_name"],
                "date": request.form["date"],
                "price": float(request.form["price"]),
            },
        )
        flash("Booking confirmed successfully")
    except ServiceError as exc:
        flash(str(exc))

    return redirect(url_for("booking.index"))
