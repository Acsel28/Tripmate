from requests import HTTPError

from microservices import planning_service as planning_module
from microservices import trip_service as trip_module


def test_trip_service_returns_recommendations(trip_client, create_user, monkeypatch):
    user_id = create_user()

    def fake_request_json(method, url, **kwargs):
        return {"recommendations": [{"title": "Off-peak arrival", "detail": "Fly early.", "type": "timing"}]}

    monkeypatch.setattr(trip_module, "request_json", fake_request_json)
    response = trip_client.post(
        f"/users/{user_id}/trips",
        json={
            "source_city": "Delhi",
            "destination_city": "Goa",
            "start_date": "2026-06-10",
            "end_date": "2026-06-14",
            "budget": 1600,
            "traveler_count": 2,
        },
    )

    assert response.status_code == 201
    assert response.get_json()["recommendations"][0]["type"] == "timing"


def test_planning_service_generates_affordable_variants(planning_client, create_user, monkeypatch):
    user_id = create_user()

    def fake_request_json(method, url, **kwargs):
        if "booking-service" in url:
            return {
                "transport": [
                    {"mode": "flight", "provider": "FastAir", "price_total": 250, "duration_hours": 2.0},
                    {"mode": "bus", "provider": "SaverBus", "price_total": 120, "duration_hours": 8.0},
                ],
                "hotels": [
                    {"name": "City Stay", "price_per_night": 60, "rating": 4.1, "tier": "economy"},
                    {"name": "Premium Stay", "price_per_night": 120, "rating": 4.8, "tier": "premium"},
                ],
            }
        if "budget-service" in url:
            return {"budget": {"total_budget": 1600}, "total_expenses": 200, "remaining": 1400}
        return {"id": 1}

    monkeypatch.setattr(planning_module, "request_json", fake_request_json)
    response = planning_client.post(
        f"/users/{user_id}/plan",
        json={
            "source_city": "Delhi",
            "destination_city": "Goa",
            "start_date": "2026-06-10",
            "end_date": "2026-06-14",
            "budget": 1600,
            "traveler_count": 2,
            "preferences": {"activity_level": "medium"},
        },
    )

    payload = response.get_json()
    assert response.status_code == 200
    assert len(payload["plans"]) == 3
    assert any(plan["plan_type"] == "cheapest" for plan in payload["plans"])
    assert payload["plans"][0]["cost_breakdown"]["total_cost"] > 0


def test_planning_service_rejects_invalid_dates(planning_client, create_user):
    user_id = create_user()
    response = planning_client.post(
        f"/users/{user_id}/plan",
        json={
            "source_city": "Delhi",
            "destination_city": "Goa",
            "start_date": "2026-06-20",
            "end_date": "2026-06-10",
            "budget": 1600,
        },
    )

    assert response.status_code == 400
    assert "End date" in response.get_json()["error"]


def test_planning_service_handles_no_routes(planning_client, create_user, monkeypatch):
    user_id = create_user()

    def fake_request_json(method, url, **kwargs):
        if "booking-service" in url:
            return {"transport": [], "hotels": [], "activities": []}
        return {"budget": {"total_budget": 1600}, "total_expenses": 0, "remaining": 1600}

    monkeypatch.setattr(planning_module, "request_json", fake_request_json)
    response = planning_client.post(
        f"/users/{user_id}/plan",
        json={
            "source_city": "Delhi",
            "destination_city": "Atlantis",
            "start_date": "2026-06-10",
            "end_date": "2026-06-14",
            "budget": 1600,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "No travel routes are available for the selected trip."


def test_planning_service_handles_booking_service_failure(planning_client, create_user, monkeypatch):
    user_id = create_user()

    def failing_request_json(method, url, **kwargs):
        if "booking-service" in url:
            error = HTTPError("service down")
            error.response = None
            raise error
        return {"budget": None, "total_expenses": 0, "remaining": None}

    monkeypatch.setattr(planning_module, "request_json", failing_request_json)
    response = planning_client.post(
        f"/users/{user_id}/plan",
        json={
            "source_city": "Delhi",
            "destination_city": "Goa",
            "start_date": "2026-06-10",
            "end_date": "2026-06-14",
            "budget": 1600,
        },
    )

    assert response.status_code == 503
    assert response.get_json()["error"] == "Booking service is unavailable."


def test_expense_service_requires_budget_first(expense_client, create_user):
    user_id = create_user()
    response = expense_client.post(
        f"/users/{user_id}/expenses",
        json={"category": "Meals", "amount": 50, "date": "2026-06-10"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Please set a budget first."
