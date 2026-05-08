import os

import requests


REQUEST_TIMEOUT = 5


def _base_url(service_name):
    service_urls = {
        "auth": os.environ.get("AUTH_SERVICE_URL", "http://localhost:5001"),
        "itinerary": os.environ.get("ITINERARY_SERVICE_URL", "http://localhost:5002"),
        "booking": os.environ.get("BOOKING_SERVICE_URL", "http://localhost:5003"),
        "budget": os.environ.get("BUDGET_SERVICE_URL", "http://localhost:5004"),
        "reporting": os.environ.get("REPORTING_SERVICE_URL", "http://localhost:5005"),
        "planning": os.environ.get("PLANNING_SERVICE_URL", "http://localhost:5006"),
        "notification": os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5007"),
        "recommendation": os.environ.get("RECOMMENDATION_SERVICE_URL", "http://localhost:5008"),
        "trip": os.environ.get("TRIP_SERVICE_URL", "http://localhost:5009"),
        "expense": os.environ.get("EXPENSE_SERVICE_URL", "http://localhost:5010"),
    }
    return service_urls[service_name].rstrip("/")


def _request(method, service_name, path, **kwargs):
    return requests.request(
        method,
        f"{_base_url(service_name)}{path}",
        timeout=REQUEST_TIMEOUT,
        **kwargs,
    )


def get_json(service_name, path, **kwargs):
    response = _request("GET", service_name, path, **kwargs)
    response.raise_for_status()
    return response.json()


def post_json(service_name, path, payload):
    response = _request("POST", service_name, path, json=payload)
    response.raise_for_status()
    return response.json()


def delete(service_name, path):
    response = _request("DELETE", service_name, path)
    response.raise_for_status()
    return response.json() if response.content else {}
