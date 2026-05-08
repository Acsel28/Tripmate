from flask import Flask, jsonify, request

from microservices.common import configure_metrics, db_cursor, dict_from_row, json_error, rows_to_dicts


def create_app():
    app = Flask(__name__)
    configure_metrics(app)

    @app.get("/health")
    def health():
        return jsonify({"service": "notification", "status": "ok"})

    @app.get("/users/<int:user_id>/notifications")
    def list_notifications(user_id):
        conn, cursor = db_cursor()
        rows = cursor.execute(
            "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
            (user_id,),
        ).fetchall()
        conn.close()
        return jsonify(rows_to_dicts(rows))

    @app.post("/users/<int:user_id>/notifications")
    def create_notification(user_id):
        payload = request.get_json(silent=True) or {}
        title = payload.get("title", "").strip()
        message = payload.get("message", "").strip()
        level = payload.get("level", "info").strip() or "info"
        channel = payload.get("channel", "in-app").strip() or "in-app"

        if not title or not message:
            return json_error("Title and message are required.", 400)

        conn, cursor = db_cursor()
        cursor.execute(
            """
            INSERT INTO notifications (user_id, channel, level, title, message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, channel, level, title, message),
        )
        notification_id = cursor.lastrowid
        conn.commit()
        row = cursor.execute("SELECT * FROM notifications WHERE id = ?", (notification_id,)).fetchone()
        conn.close()

        response = jsonify(dict_from_row(row))
        response.status_code = 201
        return response

    return app
