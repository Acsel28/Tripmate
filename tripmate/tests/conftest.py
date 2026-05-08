import os
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db import get_db
from init_db import init_db
from models.user import User
from utils.password import hash_password
from microservices.auth_service import create_app as create_auth_service
from microservices.itinerary_service import create_app as create_itinerary_service
from microservices.booking_service import create_app as create_booking_service
from microservices.budget_service import create_app as create_budget_service
from microservices.reporting_service import create_app as create_reporting_service
from microservices.notification_service import create_app as create_notification_service
from microservices.recommendation_service import create_app as create_recommendation_service
from microservices.trip_service import create_app as create_trip_service
from microservices.planning_service import create_app as create_planning_service
from microservices.expense_service import create_app as create_expense_service


@pytest.fixture(scope="session", autouse=True)
def configure_path():
    os.environ["TRIPMATE_SECRET_KEY"] = "test-secret-key"
    yield
    os.environ.pop("TRIPMATE_SECRET_KEY", None)


@pytest.fixture()
def temp_db():
    temp_dir = tempfile.TemporaryDirectory()
    db_path = Path(temp_dir.name) / "test_tripmate.db"
    os.environ["TRIPMATE_DB_PATH"] = str(db_path)
    init_db()
    yield db_path
    os.environ.pop("TRIPMATE_DB_PATH", None)
    temp_dir.cleanup()


def _build_client(app_factory):
    app = app_factory()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture()
def auth_client(temp_db):
    yield _build_client(create_auth_service)


@pytest.fixture()
def itinerary_client(temp_db):
    yield _build_client(create_itinerary_service)


@pytest.fixture()
def booking_client(temp_db):
    yield _build_client(create_booking_service)


@pytest.fixture()
def budget_client(temp_db):
    yield _build_client(create_budget_service)


@pytest.fixture()
def reporting_client(temp_db):
    yield _build_client(create_reporting_service)


@pytest.fixture()
def notification_client(temp_db):
    yield _build_client(create_notification_service)


@pytest.fixture()
def recommendation_client(temp_db):
    yield _build_client(create_recommendation_service)


@pytest.fixture()
def trip_client(temp_db):
    yield _build_client(create_trip_service)


@pytest.fixture()
def planning_client(temp_db):
    yield _build_client(create_planning_service)


@pytest.fixture()
def expense_client(temp_db):
    yield _build_client(create_expense_service)


@pytest.fixture()
def create_user():
    def _create_user(name="Test User", email="test@example.com", password="secret123"):
        conn = get_db()
        user_id = User.create(name, email, hash_password(password), conn)
        conn.close()
        return user_id

    return _create_user
