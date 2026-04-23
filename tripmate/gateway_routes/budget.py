from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from gateway_routes.client import ServiceError, finance_get, finance_post

bp = Blueprint("budget", __name__, url_prefix="/budget")


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
        payload = finance_get("/api/budget", params={"user_id": session["user_id"]})
        budget = AttrDict(payload["budget"]) if payload.get("budget") else None
        expenses = to_attr_list(payload.get("expenses", []))
        total_expenses = payload.get("total_expenses", 0)
        remaining = payload.get("remaining", 0)
    except ServiceError as exc:
        flash(str(exc))
        budget = None
        expenses = []
        total_expenses = 0
        remaining = 0

    return render_template(
        "budget.html",
        budget=budget,
        expenses=expenses,
        total_expenses=total_expenses,
        remaining=remaining,
    )


@bp.route("/set_budget", methods=["POST"])
@login_required
def set_budget():
    try:
        finance_post(
            "/api/budget",
            {
                "user_id": session["user_id"],
                "total_budget": float(request.form["total_budget"]),
            },
        )
        flash("Budget set successfully")
    except ServiceError as exc:
        flash(str(exc))

    return redirect(url_for("budget.index"))


@bp.route("/add_expense", methods=["POST"])
@login_required
def add_expense():
    try:
        finance_post(
            "/api/expenses",
            {
                "user_id": session["user_id"],
                "category": request.form["category"],
                "amount": float(request.form["amount"]),
                "date": request.form["date"],
                "description": request.form.get("description", ""),
            },
        )
        flash("Expense added successfully")
    except ServiceError as exc:
        flash(str(exc))

    return redirect(url_for("budget.index"))
