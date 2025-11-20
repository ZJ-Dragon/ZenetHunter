from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AttackType(str, Enum):
    KICK = "kick"  # Deauth/Disassociate
    BLOCK = "block"  # ARP Spoofing / Ban


class AttackStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"


class AttackRequest(BaseModel):
    """Request to start an attack on a device."""

    type: AttackType = Field(
        default=AttackType.KICK, description="Type of attack to perform"
    )
    duration: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Duration in seconds (for temporary attacks)",
    )

    model_config = ConfigDict(from_attributes=True)


class AttackResponse(BaseModel):
    """Response for attack operations."""

    device_mac: str = Field(..., description="Target device MAC")
    status: AttackStatus = Field(..., description="Current attack status")
    message: str | None = Field(None, description="Status message")

    model_config = ConfigDict(from_attributes=True)
