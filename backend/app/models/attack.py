from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AttackType(str, Enum):
    """Available attack/interference types for active defense."""

    KICK = "kick"  # WiFi Deauthentication/Disassociation
    BLOCK = "block"  # ARP Spoofing / Man-in-the-Middle
    DHCP_SPOOF = "dhcp_spoof"  # DHCP Spoofing (redirect to controlled server)
    DNS_SPOOF = "dns_spoof"  # DNS Spoofing (redirect DNS queries)
    ICMP_REDIRECT = "icmp_redirect"  # ICMP Redirect (route manipulation)
    PORT_SCAN = "port_scan"  # Port Scanning (reconnaissance)
    TRAFFIC_SHAPE = "traffic_shape"  # Traffic Shaping (bandwidth limiting)
    MAC_FLOOD = "mac_flood"  # MAC Flooding (switch table exhaustion)
    VLAN_HOP = "vlan_hop"  # VLAN Hopping (if applicable)
    BEACON_FLOOD = "beacon_flood"  # WiFi Beacon Flood (AP confusion)


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
