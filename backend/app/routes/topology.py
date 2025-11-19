from fastapi import APIRouter, Depends

from app.models.topology import NetworkTopology
from app.services.state import StateManager, get_state_manager

router = APIRouter(prefix="/topology", tags=["topology"])


@router.get("", response_model=NetworkTopology)
async def get_topology(state: StateManager = Depends(get_state_manager)):
    """Get the current network topology."""
    return state.get_topology()
