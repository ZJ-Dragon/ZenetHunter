from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class DefenseType(str, Enum):
    """Available defense strategies."""

    QUARANTINE = "quarantine"  # Complete isolation (local & wan)
    BLOCK_WAN = "block_wan"  # Block internet access only
    SYN_PROXY = "syn_proxy"  # SYN Flood protection (Global/Gateway)
    UDP_RATE_LIMIT = "udp_rate_limit"  # UDP Traffic Shaping/Rate Limiting (Global)
    ARP_DAI = "arp_dai"  # ARP Dynamic Inspection (Switch/Passive Monitoring)
    DNS_RPZ = "dns_rpz"  # DNS Response Policy Zone (Sinkhole/Redirect)
    TCP_RESET_POLICY = "tcp_reset_policy"  # TCP Reset for unauthorized traffic
    # Future: LIMIT_SPEED, etc.


class DefenseStatus(str, Enum):
    """Current status of defense on a device."""

    INACTIVE = "inactive"
    ACTIVE = "active"
    PENDING = "pending"  # Transitioning
    ERROR = "error"


class DefensePolicy(BaseModel):
    """Definition of a defense policy available to the user."""

    id: DefenseType = Field(..., description="Policy identifier")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Description of what the policy does")

    model_config = ConfigDict(from_attributes=True)


class DefenseApplyRequest(BaseModel):
    """Request to apply a defense policy on a device."""

    policy: DefenseType = Field(..., description="Defense policy to apply")
    # Defense is usually persistent until stopped, unlike attack which has duration.
    # But we might want an optional timeout? For now, keep it simple (persistent).

    model_config = ConfigDict(from_attributes=True)


class DefenseResponse(BaseModel):
    """Response for defense operations."""

    device_mac: str = Field(..., description="Target device MAC")
    status: DefenseStatus = Field(..., description="Current defense status")
    active_policy: DefenseType | None = Field(
        None, description="Currently active policy"
    )
    message: str | None = Field(None, description="Status message")

    model_config = ConfigDict(from_attributes=True)
