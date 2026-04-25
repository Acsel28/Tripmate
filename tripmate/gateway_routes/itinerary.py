from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from gateway_routes.client import ServiceError, travel_delete, travel_get, travel_post

bp = Blueprint("itinerary", __name__, url_prefix="/itinerary")


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
        payload = travel_get("/api/itineraries", params={"user_id": session["user_id"]})
        itineraries = to_attr_list(payload.get("itineraries", []))
    except ServiceError as exc:
        flash(str(exc))
        itineraries = []

    return render_template("itinerary.html", itineraries=itineraries)


@bp.route("/create", methods=["POST"])
@login_required
def create():
    title = request.form["title"]
    start_date = request.form["start_date"]
    end_date = request.form["end_date"]
    try:
        travel_post(
            "/api/itineraries",
            {
                "user_id": session["user_id"],
                "title": title,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        flash("Itinerary created successfully")
    except ServiceError as exc:
        flash(str(exc))

    return redirect(url_for("itinerary.index"))


@bp.route("/<int:itinerary_id>")
@login_required
def view(itinerary_id):
    try:
        payload = travel_get(f"/api/itineraries/{itinerary_id}", params={"user_id": session["user_id"]})
        itinerary = AttrDict(payload["itinerary"])
        destinations = to_attr_list(payload.get("destinations", []))
        return render_template("itinerary_detail.html", itinerary=itinerary, destinations=destinations)
    except ServiceError as exc:
        flash(str(exc))
        return redirect(url_for("itinerary.index"))


@bp.route("/<int:itinerary_id>/add_destination", methods=["POST"])
@login_required
def add_destination(itinerary_id):
    try:
        payload = travel_post(
            f"/api/itineraries/{itinerary_id}/destinations",
            {
                "user_id": session["user_id"],
                "location": request.form["location"],
                "date": request.form["date"],
                "notes": request.form.get("notes", ""),
            },
        )
        flash("Destination added successfully")
        recommendations = payload.get("recommendations", [])
        if recommendations:
            flash("Suggested activities: " + ", ".join(recommendations))
    except ServiceError as exc:
        flash(str(exc))

    return redirect(url_for("itinerary.view", itinerary_id=itinerary_id))


@bp.route("/destination/<int:destination_id>/delete", methods=["POST"])
@login_required
def delete_destination(destination_id):
    itinerary_id = request.form.get("itinerary_id", type=int)
    try:
        payload = travel_delete(f"/api/destinations/{destination_id}")
        itinerary_id = payload.get("itinerary_id", itinerary_id)
        flash("Destination deleted successfully")
    except ServiceError as exc:
        flash(str(exc))

    if itinerary_id:
        return redirect(url_for("itinerary.view", itinerary_id=itinerary_id))
    return redirect(url_for("itinerary.index"))
