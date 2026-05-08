import requests


REQUEST_TIMEOUT = 5


def request_json(method, url, **kwargs):
    response = requests.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
    response.raise_for_status()
    if response.content:
        return response.json()
    return {}
