import os

from flask import Flask, jsonify, request

from db import get_db

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "notification"})


@app.post("/api/notifications")
def create_notification():
    payload = request.get_json(silent=True) or {}

    user_id = payload.get("user_id")
    title = (payload.get("title") or "").strip()
    message = (payload.get("message") or "").strip()
    event_type = (payload.get("event_type") or "generic").strip().lower()
    severity = (payload.get("severity") or "info").strip().lower()

    if not user_id or not title or not message:
        return jsonify({"error": "user_id, title and message are required"}), 400

    if severity not in {"info", "warning", "critical", "success"}:
        return jsonify({"error": "severity must be one of info, warning, critical, success"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO notifications (user_id, event_type, severity, title, message)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, event_type, severity, title, message),
    )
    conn.commit()

    notification_id = cursor.lastrowid
    notification = conn.execute("SELECT * FROM notifications WHERE id = ?", (notification_id,)).fetchone()
    conn.close()

    return jsonify({"notification": dict(notification)}), 201


@app.get("/api/notifications")
def list_notifications():
    user_id = request.args.get("user_id", type=int)
    limit = request.args.get("limit", default=10, type=int)

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    safe_limit = max(1, min(limit, 100))

    conn = get_db()
    rows = conn.execute(
        """
        SELECT *
        FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (user_id, safe_limit),
    ).fetchall()
    conn.close()

    return jsonify({"notifications": [dict(row) for row in rows]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8004")))
