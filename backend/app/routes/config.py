from fastapi import APIRouter, Body, Depends, status

from app.services.state import StateManager, get_state_manager

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/lists", response_model=dict[str, list[str]])
async def get_lists(state: StateManager = Depends(get_state_manager)):
    """Get current allow and block lists."""
    return {
        "allow_list": state.get_allow_list(),
        "block_list": state.get_block_list(),
    }


@router.post("/lists/allow", status_code=status.HTTP_204_NO_CONTENT)
async def add_to_allow_list(
    mac: str = Body(
        ..., embed=True, pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
    ),
    state: StateManager = Depends(get_state_manager),
):
    """Add MAC to allow list (removes from block list)."""
    state.add_to_allow_list(mac)


@router.post("/lists/block", status_code=status.HTTP_204_NO_CONTENT)
async def add_to_block_list(
    mac: str = Body(
        ..., embed=True, pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
    ),
    state: StateManager = Depends(get_state_manager),
):
    """Add MAC to block list (removes from allow list)."""
    state.add_to_block_list(mac)


@router.delete("/lists/{mac}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_lists(mac: str, state: StateManager = Depends(get_state_manager)):
    """Remove MAC from both allow and block lists."""
    state.remove_from_lists(mac)
