from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.core.exceptions import AppError, ErrorCode
from app.models.device import Device
from app.services.state import StateManager, get_state_manager

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=List[Device])
async def list_devices(state: StateManager = Depends(get_state_manager)):
    """List all tracked devices."""
    return state.get_all_devices()


@router.get("/{mac}", response_model=Device)
async def get_device(mac: str, state: StateManager = Depends(get_state_manager)):
    """Get a specific device by MAC address."""
    device = state.get_device(mac)
    if not device:
        raise AppError(
            ErrorCode.CONFIG.NOT_FOUND,
            f"Device with MAC {mac} not found",
            extra={"mac": mac}
        )
    return device


@router.post("", response_model=Device)
async def update_device(device: Device, state: StateManager = Depends(get_state_manager)):
    """Update or add a device (Internal/Scanner use)."""
    return state.update_device(device)

