from flask import jsonify

from db import get_db

try:
    from prometheus_flask_exporter import PrometheusMetrics
except ImportError:  # pragma: no cover - optional during local editing before install
    PrometheusMetrics = None


def dict_from_row(row):
    if row is None:
        return None

    return {key: row[key] for key in row.keys()}


def rows_to_dicts(rows):
    return [dict_from_row(row) for row in rows]


def json_error(message, status_code):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response


def db_cursor():
    conn = get_db()
    return conn, conn.cursor()


def configure_metrics(app):
    if PrometheusMetrics is not None:
        PrometheusMetrics(app, path="/metrics")
    return app
