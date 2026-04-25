import os

from flask import Flask, jsonify, redirect, request

from db import get_db
from gateway_routes import auth as auth_routes
from models.user import User
from utils.password import hash_password, verify_password

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = os.environ.get("TRIPMATE_SECRET_KEY", "tripmate-secret-key-change-in-production")

PUBLIC_GATEWAY_URL = os.environ.get("PUBLIC_GATEWAY_URL", "http://localhost:8000")
PUBLIC_AUTH_URL = os.environ.get("PUBLIC_AUTH_URL", "http://localhost:8001")
PUBLIC_TRAVEL_URL = os.environ.get("PUBLIC_TRAVEL_URL", "http://localhost:8002")
PUBLIC_FINANCE_URL = os.environ.get("PUBLIC_FINANCE_URL", "http://localhost:8003")

app.register_blueprint(auth_routes.bp)


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
        }
    }


@app.get("/")
def root():
    return redirect("/auth/login")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "auth"})


@app.post("/api/auth/register")
def register():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "").strip()
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db()
    existing_user = User.get_by_email(email, conn)
    if existing_user:
        conn.close()
        return jsonify({"error": "Email already registered"}), 409

    user_id = User.create(name, email, hash_password(password), conn)
    conn.close()

    return jsonify({"id": user_id, "name": name, "email": email}), 201


@app.post("/api/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")

    if not email or not password:
        return jsonify({"error": "Missing credentials"}), 400

    conn = get_db()
    user = User.get_by_email(email, conn)
    conn.close()

    if not user or not verify_password(user.hashed_password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"id": user.id, "name": user.name, "email": user.email}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8001")))
