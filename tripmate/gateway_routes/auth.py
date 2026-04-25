import os

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from gateway_routes.client import ServiceError, auth_post

bp = Blueprint("auth", __name__, url_prefix="/auth")


def dashboard_redirect_url():
    public_gateway_url = os.environ.get("PUBLIC_GATEWAY_URL", "").rstrip("/")
    if public_gateway_url:
        return f"{public_gateway_url}/dashboard"
    return url_for("dashboard")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            auth_post(
                "/api/auth/register",
                {
                    "name": request.form["name"],
                    "email": request.form["email"],
                    "password": request.form["password"],
                },
            )
            flash("Registration successful! Please login.")
            return redirect(url_for("auth.login"))
        except ServiceError as exc:
            flash(str(exc))
            return redirect(url_for("auth.register"))

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            payload = auth_post(
                "/api/auth/login",
                {
                    "email": request.form["email"],
                    "password": request.form["password"],
                },
            )
            session["user_id"] = payload["id"]
            session["user_name"] = payload["name"]
            return redirect(dashboard_redirect_url())
        except ServiceError as exc:
            flash(str(exc))

    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
