import pytest
from fastapi.testclient import TestClient

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


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token():
    return create_access_token(data={"sub": "admin", "role": "admin"})


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
