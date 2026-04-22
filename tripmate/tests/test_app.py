from db import get_db
from models.user import User
from utils.password import hash_password


def create_user(name="Test User", email="test@example.com", password="secret123"):
    conn = get_db()
    user_id = User.create(name, email, hash_password(password), conn)
    conn.close()
    return user_id


def login(client, email="test@example.com", password="secret123"):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def test_index_redirects_to_login_for_anonymous_user(client):
    response = client.get("/")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_register_creates_user_and_redirects_to_login(client):
    response = client.post(
        "/auth/register",
        data={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Registration successful! Please login." in response.data


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_login_redirects_to_dashboard(client):
    create_user()

    response = login(client)

    assert response.status_code == 200
    assert b"Welcome, Test User!" in response.data


def test_budget_can_be_created_for_logged_in_user(client):
    create_user()
    login(client)

    response = client.post(
        "/budget/set_budget",
        data={"total_budget": "2500"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Budget set successfully" in response.data
    assert b"2500.0" in response.data


def test_expense_requires_existing_budget(client):
    create_user()
    login(client)

    response = client.post(
        "/budget/add_expense",
        data={
            "category": "Transport",
            "amount": "120",
            "date": "2026-04-22",
            "description": "Airport taxi",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Please set a budget first" in response.data


def test_expense_is_added_when_budget_exists(client):
    create_user()
    login(client)
    client.post("/budget/set_budget", data={"total_budget": "2500"}, follow_redirects=True)

    response = client.post(
        "/budget/add_expense",
        data={
            "category": "Transport",
            "amount": "120",
            "date": "2026-04-22",
            "description": "Airport taxi",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Expense added successfully" in response.data
    assert b"Transport" in response.data
