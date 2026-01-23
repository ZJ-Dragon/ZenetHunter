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


@router.patch("/{mac}", response_model=Device, summary="Update device information")
async def patch_device(
    mac: str = Path(..., pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"),
    request: DeviceUpdateRequest = ...,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: AsyncSession = Depends(get_db),
    state: StateManager = Depends(get_state_manager),
    ws=Depends(get_connection_manager),
) -> Device:
    """Update device alias and tags (admin operation).

    Args:
        mac: Device MAC address
        request: Update data (alias, tags)

    Returns:
        Updated device object
    """
    repo = DeviceRepository(db)
    device = await repo.get_by_mac(mac)
    if not device:
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND,
            f"Device with MAC {mac} not found",
            extra={"mac": mac},
        )

    # Update fields
    if request.alias is not None:
        device.alias = request.alias
    if request.tags is not None:
        import json

        device.tags = json.dumps(request.tags)

    await db.commit()
    await db.refresh(device)

    # Update state manager
    state.update_device(device)

    # Broadcast device updated event
    await ws.broadcast(
        {
            "event": "deviceUpdated",
            "data": {
                "mac": mac,
                "alias": device.alias,
                "tags": request.tags,
            },
        }
    )

    return device


@router.post(
    "/{mac}/recognition/override",
    response_model=Device,
    summary="Override automatic device recognition (admin only)",
)
async def override_recognition(
    mac: str = Path(..., pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"),
    request: RecognitionOverrideRequest = ...,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: AsyncSession = Depends(get_db),
    state: StateManager = Depends(get_state_manager),
    ws=Depends(get_connection_manager),
) -> Device:
    """Manually override automatic device recognition results.

    This endpoint allows administrators to manually confirm or correct
    device vendor, model, and type. The override is persisted and will
    not be overwritten by future automatic recognition.

    Args:
        mac: Device MAC address
        request: Override data (vendor, model, device_type)

    Returns:
        Updated device with manual override applied
    """
    repo = DeviceRepository(db)
    device = await repo.get_by_mac(mac)
    if not device:
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND,
            f"Device with MAC {mac} not found",
            extra={"mac": mac},
        )

    # Apply manual overrides
    if request.vendor is not None:
        device.vendor_guess = request.vendor
        device.vendor = request.vendor  # Also update main vendor field
    if request.model is not None:
        device.model_guess = request.model
        device.model = request.model  # Also update main model field
    if request.device_type is not None:
        from app.models.db.device import DeviceTypeEnum

        try:
            device.type = DeviceTypeEnum(request.device_type.lower())
        except ValueError:
            raise AppError(
                ErrorCode.API_BAD_REQUEST,
                f"Invalid device type: {request.device_type}",
                extra={"valid_types": [t.value for t in DeviceTypeEnum]},
            )

    # Mark as manually overridden
    device.recognition_manual_override = True
    device.recognition_confidence = 100  # Manual confirmation = 100% confidence

    # Update recognition evidence
    import json
    from datetime import UTC, datetime

    evidence = json.loads(device.recognition_evidence or "{}")
    evidence["manual_override"] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "user": current_user.username,
        "vendor": request.vendor,
        "model": request.model,
        "device_type": request.device_type,
    }
    device.recognition_evidence = json.dumps(evidence)

    await db.commit()
    await db.refresh(device)

    # Update state manager
    state.update_device(device)

    # Broadcast recognition override event
    await ws.broadcast(
        {
            "event": "recognitionOverridden",
            "data": {
                "mac": mac,
                "vendor": device.vendor,
                "model": device.model,
                "device_type": device.type.value,
                "confidence": 100,
                "manual_override": True,
            },
        }
    )

    return device
