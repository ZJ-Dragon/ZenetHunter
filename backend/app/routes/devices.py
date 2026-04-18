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
from app.models.device import Device, DeviceType
from app.repositories.device import UNSET, DeviceRepository
from app.repositories.device_fingerprint import DeviceFingerprintRepository
from app.repositories.event_log import EventLogRepository
from app.services.fingerprint_key import generate_fingerprint_key
from app.services.manual_profile_service import (
    ManualProfileService,
    build_match_keys,
)
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


def _load_recognition_evidence(device: Device) -> dict:
    """Return recognition evidence as a mutable dictionary."""
    if isinstance(device.recognition_evidence, dict):
        return dict(device.recognition_evidence)
    if isinstance(device.recognition_evidence, str):
        try:
            return json.loads(device.recognition_evidence)
        except json.JSONDecodeError:
            return {}
    return {}


def _fingerprint_model_to_payload(record) -> dict | None:
    """Serialize a persisted fingerprint row into the matching payload shape."""
    if record is None:
        return None

    def _maybe_json(value):
        if not value:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    payload = {
        "dhcp_opt12_hostname": record.dhcp_opt12_hostname,
        "dhcp_opt55_prl": record.dhcp_opt55_prl,
        "dhcp_opt60_vci": record.dhcp_opt60_vci,
        "user_agent": record.user_agent,
        "mdns_services": _maybe_json(record.mdns_services),
        "ssdp_server": _maybe_json(record.ssdp_server),
        "ja3": record.ja3,
    }
    return {key: value for key, value in payload.items() if value is not None}


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
    updated_device = await repo.update_metadata(
        mac,
        alias=request.alias if request.alias is not None else UNSET,
        tags=request.tags if request.tags is not None else UNSET,
    )
    if not updated_device:
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND,
            f"Device with MAC {mac} not found",
            extra={"mac": mac},
        )

    await db.commit()

    # Update state manager
    state.update_device(updated_device)

    # Broadcast device updated event
    await ws.broadcast(
        {
            "event": "deviceUpdated",
            "data": {
                "mac": mac,
                "alias": updated_device.alias,
                "tags": updated_device.tags,
                "display_name": updated_device.display_name,
                "display_vendor": updated_device.display_vendor,
            },
        }
    )

    return updated_device


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

    device_type = None
    if request.device_type is not None:
        try:
            device_type = DeviceType(request.device_type.lower())
        except ValueError:
            raise AppError(
                ErrorCode.API_BAD_REQUEST,
                f"Invalid device type: {request.device_type}",
                extra={"valid_types": [t.value for t in DeviceType]},
            ) from None

    evidence = _load_recognition_evidence(device)
    evidence["manual_override"] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "user": current_user.username,
        "vendor": request.vendor,
        "model": request.model,
        "device_type": request.device_type,
    }

    updated_device = await repo.apply_recognition_override(
        mac,
        vendor=request.vendor,
        model=request.model,
        device_type=device_type,
        evidence=evidence,
    )
    if not updated_device:
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND,
            f"Failed to update device {mac}",
            extra={"mac": mac},
        )

    await db.commit()

    # Update state manager
    state.update_device(updated_device)

    # Broadcast recognition override event
    await ws.broadcast(
        {
            "event": "recognitionOverridden",
            "data": {
                "mac": mac,
                "vendor": updated_device.vendor,
                "model": updated_device.model,
                "device_type": updated_device.type.value,
                "confidence": 100,
                "manual_override": True,
            },
        }
    )

    return updated_device


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
    fingerprint_repo = DeviceFingerprintRepository(db)
    manual_profile_service = ManualProfileService(db)
    event_repo = EventLogRepository(db)

    # Get existing device
    device = await device_repo.get_by_mac(mac)
    if not device:
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND,
            f"Device with MAC {mac} not found",
            extra={"mac": mac},
        )

    # Generate fingerprint key from persisted fingerprint signals if available.
    fingerprint_data = _fingerprint_model_to_payload(
        await fingerprint_repo.get_by_mac(mac)
    )

    fingerprint_key, components = generate_fingerprint_key(
        fingerprint_data=fingerprint_data,
        mac=mac,
        vendor_guess=device.vendor_guess,
        model_guess=device.model_guess,
    )

    match_keys = build_match_keys(
        mac=mac,
        fingerprint_components=components,
        vendor_guess=device.vendor_guess,
        model_guess=device.model_guess,
    )

    profile = await manual_profile_service.create_or_update_profile(
        mac=mac,
        manual_name=request.name_manual,
        manual_vendor=request.vendor_manual,
        fingerprint_key=fingerprint_key,
        match_keys=match_keys,
        ip_hint=str(device.ip),
    )

    bound_model = await device_repo.bind_manual_profile(
        mac=mac,
        profile_id=profile.profile_id,
        updated_by=current_user.username,
        manual_name=profile.manual_name,
        manual_vendor=profile.manual_vendor,
    )

    if not bound_model:
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND,
            f"Failed to update device {mac}",
            extra={"mac": mac},
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
            "manual_profile_id": profile.profile_id,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )

    await db.commit()

    # Convert to domain model for response
    updated_device = await device_repo.get_by_mac(mac)
    if not updated_device:
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND,
            f"Device with MAC {mac} not found",
            extra={"mac": mac},
        )

    # Update state manager
    state.update_device(updated_device)

    # Broadcast device updated event via WebSocket
    await ws.broadcast(
        {
            "event": "deviceUpdated",
            "data": {
                "mac": mac,
                "display_name": updated_device.display_name,
                "display_vendor": updated_device.display_vendor,
                "name_manual": updated_device.name_manual,
                "vendor_manual": updated_device.vendor_manual,
                "manual_override": True,
                "manual_profile_id": profile.profile_id,
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

    # Clear manual labels/binding
    cleared_model = await device_repo.clear_manual_profile(
        mac=mac, updated_by=current_user.username
    )

    if not cleared_model:
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
    updated_device = await device_repo.get_by_mac(mac)
    if not updated_device:
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND,
            f"Device with MAC {mac} not found",
            extra={"mac": mac},
        )

    # Update state manager
    state.update_device(updated_device)

    # Broadcast device updated event
    await ws.broadcast(
        {
            "event": "deviceUpdated",
            "data": {
                "mac": mac,
                "display_name": updated_device.display_name,
                "display_vendor": updated_device.display_vendor,
                "name_manual": updated_device.name_manual,
                "vendor_manual": updated_device.vendor_manual,
                "manual_override": False,
                "manual_profile_id": None,
                "updated_by": current_user.username,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }
    )

    logger.info(f"Manual label cleared for {mac} by {current_user.username}")

    return updated_device
