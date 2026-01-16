from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress

from app.models.attack import AttackStatus
from app.models.defender import DefenseStatus, DefenseType


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
    attack_status: AttackStatus = Field(
        default=AttackStatus.IDLE, description="Current attack status"
    )
    defense_status: DefenseStatus = Field(
        default=DefenseStatus.INACTIVE, description="Current defense status"
    )
    active_defense_policy: DefenseType | None = Field(
        default=None, description="Currently active defense policy"
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

    model_config = ConfigDict(from_attributes=True)
