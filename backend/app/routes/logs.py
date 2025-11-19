from fastapi import APIRouter, Depends, Query

from app.models.log import SystemLog
from app.services.state import StateManager, get_state_manager

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=list[SystemLog])
async def get_logs(
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    state: StateManager = Depends(get_state_manager),
):
    """Get recent system logs."""
    return state.get_logs(limit=limit)


@router.post("", response_model=None, status_code=201)
async def add_log(log: SystemLog, state: StateManager = Depends(get_state_manager)):
    """Add a system log entry."""
    state.add_log(log)
