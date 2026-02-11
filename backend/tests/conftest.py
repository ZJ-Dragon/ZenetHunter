import asyncio
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from app.core.database import init_db
from app.main import app
from app.services.auth import create_access_token
from app.services.state import get_state_manager


@pytest.fixture(autouse=True)
def reset_state():
    """Reset the singleton StateManager before each test."""
    from app.services.state import StateManager

    # Force reset singleton instance for complete isolation
    StateManager._instance = None
    StateManager._initialized = False
    state = get_state_manager()
    state.reset()


@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    """
    Ensure the database schema exists before tests run.

    Uses a temporary SQLite file to avoid polluting local data.
    """
    db_dir = tempfile.mkdtemp(prefix="zh-test-db-")
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_dir}/test.db"
    # Enable active defense for tests to avoid 400 responses
    os.environ["ACTIVE_DEFENSE_ENABLED"] = "true"
    os.environ["ACTIVE_DEFENSE_READONLY"] = "false"
    # Reset database singletons if they were created earlier
    from app.core import database

    database._engine = None
    database._session_factory = None

    asyncio.run(init_db())
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token():
    return create_access_token(data={"sub": "admin", "role": "admin"})


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
