from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppError, ErrorCode
from app.models.device import Device
from app.repositories.device import DeviceRepository
from app.services.state import StateManager, get_state_manager

router = APIRouter(prefix="/devices", tags=["devices"])


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
