from unittest.mock import patch

from app import app


def test_invalid_input_missing_field():
    client = app.test_client()
    response = client.post("/plan", json={"source_city": "Delhi"})
    assert response.status_code == 400


@patch("app.fetch_json")
def test_api_failure_handling(mock_fetch):
    mock_fetch.side_effect = RuntimeError("downstream unavailable")
    client = app.test_client()
    payload = {
        "source_city": "Delhi",
        "destination_city": "Mumbai",
        "start_date": "2026-05-01",
        "end_date": "2026-05-05",
        "budget": 10000,
        "preferences": {"transport_type": "flight", "hotel_type": "budget"},
    }
    response = client.post("/plan", json=payload)
    assert response.status_code == 503
