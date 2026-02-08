from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress

from app.models.attack import ActiveDefenseStatus
from app.models.manual_profile import DeviceManualProfile


class DeviceType(str, Enum):
    UNKNOWN = "unknown"
    ROUTER = "router"
    PC = "pc"
    MOBILE = "mobile"
    IOT = "iot"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BLOCKED = "blocked"


class Device(BaseModel):
    """Device model representing a network host."""

    mac: str = Field(
        ...,
        description="MAC address of the device",
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
    )
    ip: IPvAnyAddress = Field(..., description="IP address of the device")
    name: str | None = Field(None, description="Hostname or alias")
    vendor: str | None = Field(None, description="Device vendor resolved from MAC OUI")
    model: str | None = Field(
        None, description="Device model resolved from MAC address"
    )
    type: DeviceType = Field(
        default=DeviceType.UNKNOWN, description="Device type category"
    )
    status: DeviceStatus = Field(
        default=DeviceStatus.ONLINE, description="Current connection status"
    )
    active_defense_status: ActiveDefenseStatus = Field(
        default=ActiveDefenseStatus.IDLE,
        description="Current active defense operation status",
    )
    first_seen: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when device was first detected",
    )
    last_seen: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when device was last active",
    )
    tags: list[str] | None = Field(
        default_factory=list, description="Tags associated with the device"
    )
    alias: str | None = Field(None, description="User-friendly alias for the device")
    manual_profile_id: int | None = Field(
        None, description="Bound manual profile ID (long-lived)"
    )
    manual_profile: DeviceManualProfile | None = Field(
        None, description="Manual profile details"
    )
    # Recognition fields
    vendor_guess: str | None = Field(
        None, description="Vendor guess from multi-signal recognition"
    )
    model_guess: str | None = Field(
        None, description="Model guess from multi-signal recognition"
    )
    recognition_confidence: int | None = Field(
        None, ge=0, le=100, description="Recognition confidence score (0-100)"
    )
    recognition_evidence: dict[str, Any] | None = Field(
        None, description="Recognition evidence (matched fields, sources, weights)"
    )

    # Manual override fields (user-provided labels)
    name_manual: str | None = Field(
        None, description="User-provided device name (takes priority)"
    )
    vendor_manual: str | None = Field(
        None, description="User-provided vendor name (takes priority)"
    )
    manual_override_at: datetime | None = Field(
        None, description="When manual override was applied"
    )
    manual_override_by: str | None = Field(
        None, description="Username who applied the manual override"
    )

    # Scanning metadata (hybrid scanner)
    discovery_source: str | None = Field(
        None,
        description="Discovery source: candidate-cache/dhcp/refresh/enrich/full-scan",
    )
    freshness_score: int | None = Field(
        None,
        ge=0,
        le=100,
        description="Data freshness score (0=stale, 100=just confirmed)",
    )
    # Display helpers (manual > alias > auto)
    display_name: str | None = Field(
        None, description="Highest priority name for UI rendering"
    )
    display_vendor: str | None = Field(
        None, description="Highest priority vendor for UI rendering"
    )
    name_auto: str | None = Field(
        None, description="Automatically derived name/hostname"
    )
    vendor_auto: str | None = Field(None, description="Automatically derived vendor")

    model_config = ConfigDict(from_attributes=True)


class DeviceUpdateRequest(BaseModel):
    """Request model for updating device manual labels."""

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

    model_config = ConfigDict(str_strip_whitespace=True)
