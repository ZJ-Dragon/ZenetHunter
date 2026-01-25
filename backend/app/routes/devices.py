import json
import logging
import re
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppError, ErrorCode
from app.core.security import get_current_user
from app.models.auth import User
from app.models.device import Device
from app.repositories.device import DeviceRepository
from app.repositories.event_log import EventLogRepository
from app.repositories.manual_override import ManualOverrideRepository
from app.services.fingerprint_key import generate_fingerprint_key
from app.services.state import StateManager, get_state_manager
from app.services.websocket import get_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/devices", tags=["devices"])


class DeviceUpdateRequest(BaseModel):
    """Request to update device information."""

    alias: str | None = Field(None, description="User-friendly device alias")
    tags: list[str] | None = Field(None, description="Device tags")


class ManualLabelRequest(BaseModel):
    """Request to manually label device name and vendor."""

    name_manual: str | None = Field(
        None,
        max_length=255,
        description="User-provided device name",
    )
    vendor_manual: str | None = Field(
        None,
        max_length=255,
        description="User-provided vendor name",
    )

    @field_validator("name_manual", "vendor_manual", mode="before")
    @classmethod
    def sanitize_string(cls, v: str | None) -> str | None:
        """Sanitize input to prevent injection and log pollution."""
        if v is None:
            return None
        # Strip whitespace
        v = v.strip()
        if not v:
            return None
        # Remove control characters and limit to safe ASCII + common Unicode
        v = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", v)
        # Limit length (already enforced by Field, but double-check)
        return v[:255] if len(v) > 255 else v


class ManualLabelResponse(BaseModel):
    """Response for manual label update."""

    device: Device
    fingerprint_key: str
    message: str


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
            ) from None

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


@router.put(
    "/{mac}/manual-label",
    response_model=ManualLabelResponse,
    summary="Manually label device name and vendor (admin only)",
)
async def update_manual_label(
    mac: str = Path(..., pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"),
    request: ManualLabelRequest = ...,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: AsyncSession = Depends(get_db),
    state: StateManager = Depends(get_state_manager),
    ws=Depends(get_connection_manager),
) -> ManualLabelResponse:
    """Manually label a device's name and vendor.

    This endpoint allows administrators to provide custom names and vendor
    labels for devices. These manual labels:
    - Take priority over automatic recognition results
    - Are stored in the database for persistence
    - Generate a fingerprint key for future device matching
    - Can be automatically applied to similar devices

    Args:
        mac: Device MAC address
        request: Manual label data (name_manual, vendor_manual)

    Returns:
        ManualLabelResponse with updated device and fingerprint key
    """
    device_repo = DeviceRepository(db)
    override_repo = ManualOverrideRepository(db)
    event_repo = EventLogRepository(db)

    # Get existing device
    device = await device_repo.get_by_mac(mac)
    if not device:
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND,
            f"Device with MAC {mac} not found",
            extra={"mac": mac},
        )

    # Generate fingerprint key from device characteristics
    # Try to get fingerprint data if available
    fingerprint_data = None
    if device.recognition_evidence:
        fingerprint_data = device.recognition_evidence

    fingerprint_key, components = generate_fingerprint_key(
        fingerprint_data=fingerprint_data,
        mac=mac,
        vendor_guess=device.vendor_guess,
        model_guess=device.model_guess,
    )

    # Update device manual labels
    updated_model = await device_repo.update_manual_labels(
        mac=mac,
        name_manual=request.name_manual,
        vendor_manual=request.vendor_manual,
        updated_by=current_user.username,
    )

    if not updated_model:
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND,
            f"Failed to update device {mac}",
            extra={"mac": mac},
        )

    # Store/update manual override for fingerprint-based matching
    await override_repo.upsert(
        fingerprint_key=fingerprint_key,
        manual_name=request.name_manual,
        manual_vendor=request.vendor_manual,
        source_mac=mac,
        source_ip=str(device.ip),
        fingerprint_components=components,
        username=current_user.username,
    )

    # Audit log the change
    await event_repo.add_log(
        level="INFO",
        module="manual_label",
        message=f"Manual label updated for device {mac}",
        device_mac=mac,
        context={
            "action": "manual_label_update",
            "user": current_user.username,
            "name_manual": request.name_manual,
            "vendor_manual": request.vendor_manual,
            "fingerprint_key": fingerprint_key,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )

    await db.commit()

    # Convert to domain model for response
    updated_device = device_repo.to_domain_model(updated_model)

    # Update state manager
    state.update_device(updated_device)

    # Broadcast device updated event via WebSocket
    await ws.broadcast(
        {
            "event": "deviceUpdated",
            "data": {
                "mac": mac,
                "name_manual": request.name_manual,
                "vendor_manual": request.vendor_manual,
                "manual_override": True,
                "fingerprint_key": fingerprint_key,
                "updated_by": current_user.username,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }
    )

    logger.info(
        f"Manual label updated for {mac} by {current_user.username}: "
        f"name={request.name_manual}, vendor={request.vendor_manual}"
    )

    return ManualLabelResponse(
        device=updated_device,
        fingerprint_key=fingerprint_key,
        message="Manual label updated successfully",
    )


@router.delete(
    "/{mac}/manual-label",
    response_model=Device,
    summary="Clear manual labels for a device (admin only)",
)
async def clear_manual_label(
    mac: str = Path(..., pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"),
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: AsyncSession = Depends(get_db),
    state: StateManager = Depends(get_state_manager),
    ws=Depends(get_connection_manager),
) -> Device:
    """Clear manual labels from a device.

    This reverts the device to using automatic recognition results.

    Args:
        mac: Device MAC address

    Returns:
        Updated device with manual labels cleared
    """
    device_repo = DeviceRepository(db)
    event_repo = EventLogRepository(db)

    # Get existing device
    device = await device_repo.get_by_mac(mac)
    if not device:
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND,
            f"Device with MAC {mac} not found",
            extra={"mac": mac},
        )

    # Clear manual labels
    updated_model = await device_repo.update_manual_labels(
        mac=mac,
        name_manual=None,
        vendor_manual=None,
        updated_by=current_user.username,
    )

    if not updated_model:
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND,
            f"Failed to update device {mac}",
            extra={"mac": mac},
        )

    # Audit log the change
    await event_repo.add_log(
        level="INFO",
        module="manual_label",
        message=f"Manual label cleared for device {mac}",
        device_mac=mac,
        context={
            "action": "manual_label_clear",
            "user": current_user.username,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )

    await db.commit()

    # Convert to domain model
    updated_device = device_repo.to_domain_model(updated_model)

    # Update state manager
    state.update_device(updated_device)

    # Broadcast device updated event
    await ws.broadcast(
        {
            "event": "deviceUpdated",
            "data": {
                "mac": mac,
                "name_manual": None,
                "vendor_manual": None,
                "manual_override": False,
                "updated_by": current_user.username,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }
    )

    logger.info(f"Manual label cleared for {mac} by {current_user.username}")

    return updated_device
