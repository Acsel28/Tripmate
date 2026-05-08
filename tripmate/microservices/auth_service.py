from flask import Flask, jsonify, request

from microservices.common import configure_metrics, db_cursor, dict_from_row, json_error
from models.user import User
from utils.password import hash_password, verify_password


def create_app():
    app = Flask(__name__)
    configure_metrics(app)

    @app.get("/health")
    def health():
        return jsonify({"service": "auth", "status": "ok"})

    @app.post("/register")
    def register():
        payload = request.get_json(silent=True) or {}
        name = payload.get("name", "").strip()
        email = payload.get("email", "").strip().lower()
        password = payload.get("password", "")

        if not name or not email or not password:
            return json_error("Name, email, and password are required.", 400)

        conn, _ = db_cursor()
        existing_user = User.get_by_email(email, conn)
        if existing_user:
            conn.close()
            return json_error("Email already registered.", 409)

        user_id = User.create(name, email, hash_password(password), conn)
        user_row = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        conn.close()

        response = jsonify(dict_from_row(user_row))
        response.status_code = 201
        return response

    @app.post("/login")
    def login():
        payload = request.get_json(silent=True) or {}
        email = payload.get("email", "").strip().lower()
        password = payload.get("password", "")

        if not email or not password:
            return json_error("Email and password are required.", 400)

        conn, _ = db_cursor()
        user = User.get_by_email(email, conn)
        if not user or not verify_password(user.hashed_password, password):
            conn.close()
            return json_error("Invalid email or password.", 401)

        user_row = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user.id,),
        ).fetchone()
        conn.close()
        return jsonify(dict_from_row(user_row))

    @app.get("/users/<int:user_id>")
    def get_user(user_id):
        conn, _ = db_cursor()
        user_row = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        conn.close()

        if not user_row:
            return json_error("User not found.", 404)

        return jsonify(dict_from_row(user_row))

    return app
