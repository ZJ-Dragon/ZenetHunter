from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress

from app.models.attack import AttackStatus


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
    type: DeviceType = Field(
        default=DeviceType.UNKNOWN, description="Device type category"
    )
    status: DeviceStatus = Field(
        default=DeviceStatus.ONLINE, description="Current connection status"
    )
    attack_status: AttackStatus = Field(
        default=AttackStatus.IDLE, description="Current attack status"
    )
    first_seen: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when device was first detected",
    )
    last_seen: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when device was last active",
    )

    model_config = ConfigDict(from_attributes=True)
