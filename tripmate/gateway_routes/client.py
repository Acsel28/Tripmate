import os

import requests

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8001")
TRAVEL_SERVICE_URL = os.environ.get("TRAVEL_SERVICE_URL", "http://localhost:8002")
FINANCE_SERVICE_URL = os.environ.get("FINANCE_SERVICE_URL", "http://localhost:8003")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:8004")
REQUEST_TIMEOUT_SECONDS = float(os.environ.get("INTERNAL_API_TIMEOUT_SECONDS", "5"))


class ServiceError(Exception):
    pass


def _request(method, base_url, path, **kwargs):
    url = f"{base_url}{path}"
    try:
        response = requests.request(method, url, timeout=REQUEST_TIMEOUT_SECONDS, **kwargs)
    except requests.RequestException as exc:
        raise ServiceError(str(exc)) from exc

    if response.status_code >= 400:
        message = f"Service request failed with status {response.status_code}"
        try:
            payload = response.json()
            if isinstance(payload, dict) and payload.get("error"):
                message = payload["error"]
        except ValueError:
            pass
        raise ServiceError(message)

    if not response.text:
        return {}

    try:
        return response.json()
    except ValueError as exc:
        raise ServiceError("Service returned non-JSON response") from exc


def auth_post(path, payload):
    return _request("POST", AUTH_SERVICE_URL, path, json=payload)


def travel_get(path, params=None):
    return _request("GET", TRAVEL_SERVICE_URL, path, params=params)


def travel_post(path, payload):
    return _request("POST", TRAVEL_SERVICE_URL, path, json=payload)


def travel_delete(path):
    return _request("DELETE", TRAVEL_SERVICE_URL, path)


def finance_get(path, params=None):
    return _request("GET", FINANCE_SERVICE_URL, path, params=params)


def finance_post(path, payload):
    return _request("POST", FINANCE_SERVICE_URL, path, json=payload)


def notification_get(path, params=None):
    return _request("GET", NOTIFICATION_SERVICE_URL, path, params=params)


def notification_post(path, payload):
    return _request("POST", NOTIFICATION_SERVICE_URL, path, json=payload)
