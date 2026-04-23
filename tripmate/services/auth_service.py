from flask import Flask, jsonify, request

from db import get_db
from models.user import User
from utils.password import hash_password, verify_password

app = Flask(__name__)


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
    app.run(host="0.0.0.0", port=8001)
