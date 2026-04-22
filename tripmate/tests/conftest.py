import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture()
def client():
    temp_dir = tempfile.TemporaryDirectory()
    db_path = Path(temp_dir.name) / "test_tripmate.db"
    os.environ["TRIPMATE_DB_PATH"] = str(db_path)
    os.environ["TRIPMATE_SECRET_KEY"] = "test-secret-key"

    from app import app
    from init_db import init_db

    app.config["TESTING"] = True
    init_db()

    with app.test_client() as test_client:
        yield test_client

    os.environ.pop("TRIPMATE_DB_PATH", None)
    os.environ.pop("TRIPMATE_SECRET_KEY", None)
    temp_dir.cleanup()
