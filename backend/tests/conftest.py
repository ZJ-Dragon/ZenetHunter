import pytest

from app.services.state import get_state_manager


@pytest.fixture(autouse=True)
def reset_state():
    """Reset the singleton StateManager before each test."""
    state = get_state_manager()
    state.reset()

