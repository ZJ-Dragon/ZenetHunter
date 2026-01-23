from typing import Annotated

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppError, ErrorCode
from app.core.security import get_current_user
from app.models.auth import User
from app.models.device import Device
from app.repositories.device import DeviceRepository
from app.services.state import StateManager, get_state_manager
from app.services.websocket import get_connection_manager

router = APIRouter(prefix="/devices", tags=["devices"])


class DeviceUpdateRequest(BaseModel):
    """Request to update device information."""
    
    alias: str | None = Field(None, description="User-friendly device alias")
    tags: list[str] | None = Field(None, description="Device tags")


class RecognitionOverrideRequest(BaseModel):
    """Request to manually override automatic device recognition."""
    
    vendor: str | None = Field(None, description="Manually confirmed vendor")
    model: str | None = Field(None, description="Manually confirmed model")
    device_type: str | None = Field(None, description="Manually confirmed device type")


@router.get("", response_model=list[Device])
async def list_devices(db: AsyncSession = Depends(get_db)):
    """List all tracked devices from database."""
    repo = DeviceRepository(db)
    devices = await repo.get_all()
    return devices


@router.get("/{mac}", response_model=Device)
async def get_device(mac: str, db: AsyncSession = Depends(get_db)):
    """Get a specific device by MAC address from database."""
    repo = DeviceRepository(db)
    device = await repo.get_by_mac(mac)
    if not device:
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND,
            f"Device with MAC {mac} not found",
            extra={"mac": mac},
        )
    return device


@router.post("", response_model=Device)
async def update_device(
    device: Device,
    db: AsyncSession = Depends(get_db),
    state: StateManager = Depends(get_state_manager),
):
    """Update or add a device (Internal/Scanner use)."""
    repo = DeviceRepository(db)
    updated_device = await repo.upsert(device)
    await db.commit()

    # Also update in-memory state for immediate WebSocket notifications
    state.update_device(updated_device)

    return updated_device
