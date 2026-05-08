from flask import Flask, jsonify, request

from microservices.common import configure_metrics, json_error
from recommendation_engine import build_recommendations


def create_app():
    app = Flask(__name__)
    configure_metrics(app)

    @app.get("/health")
    def health():
        return jsonify({"service": "recommendation", "status": "ok"})

    @app.post("/recommendations")
    def recommendations():
        payload = request.get_json(silent=True) or {}
        required_fields = ["destination_city", "budget"]
        if any(not payload.get(field) for field in required_fields):
            return json_error("Destination city and budget are required.", 400)
        return jsonify({"recommendations": build_recommendations(payload)})

    return app
