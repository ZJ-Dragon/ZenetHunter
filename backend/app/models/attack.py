"""Active Defense Models for Network Security Research.

This module defines active defense strategies used in controlled network security research.
All operations are designed for authorized testing environments only.

⚠️  SECURITY RESEARCH ONLY ⚠️
This module contains implementations of active defense techniques for academic research
and authorized security testing. Unauthorized use is strictly prohibited and may be illegal.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ActiveDefenseType(str, Enum):
    """Active defense strategies for network security research.
    
    These techniques are implemented for research purposes in controlled environments.
    Each strategy serves specific security research objectives:
    
    - Device isolation and network segmentation testing
    - Intrusion response simulation
    - Network resilience evaluation
    - Attack surface analysis
    """

    # WiFi Layer Active Defense
    KICK = "kick"  # WiFi Deauthentication (802.11 deauth frame injection)
    BEACON_FLOOD = "beacon_flood"  # WiFi Beacon Flooding (AP confusion testing)
    
    # Network Layer Active Defense  
    BLOCK = "block"  # ARP Spoofing (traffic redirection/isolation)
    ARP_FLOOD = "arp_flood"  # ARP Table Poisoning (network stress testing)
    ICMP_REDIRECT = "icmp_redirect"  # ICMP Redirect (route manipulation testing)
    SYN_FLOOD = "syn_flood"  # SYN Flooding (connection exhaustion testing)
    UDP_FLOOD = "udp_flood"  # UDP Flooding (bandwidth exhaustion testing)
    
    # Protocol Layer Active Defense
    DHCP_SPOOF = "dhcp_spoof"  # DHCP Spoofing (address assignment control)
    DNS_SPOOF = "dns_spoof"  # DNS Spoofing (name resolution redirection)
    TCP_RST = "tcp_rst"  # TCP Reset Injection (connection termination)
    
    # Switch/Bridge Layer Active Defense
    MAC_FLOOD = "mac_flood"  # MAC Address Flooding (CAM table exhaustion)
    VLAN_HOP = "vlan_hop"  # VLAN Hopping (segmentation testing)
    
    # Advanced Techniques
    PORT_SCAN = "port_scan"  # Active Port Scanning (service discovery)
    TRAFFIC_SHAPE = "traffic_shape"  # Traffic Shaping (bandwidth control)


class ActiveDefenseStatus(str, Enum):
    """Status of active defense operations."""
    
    IDLE = "idle"  # No active operation running
    RUNNING = "running"  # Operation in progress
    STOPPED = "stopped"  # Operation stopped manually
    FAILED = "failed"  # Operation failed due to error


class ActiveDefenseRequest(BaseModel):
    """Request to initiate an active defense operation.
    
    Attributes:
        type: The type of active defense strategy to employ
        duration: Maximum duration in seconds (1-3600)
        intensity: Operation intensity level (1-10), default 5
    """

    type: ActiveDefenseType = Field(
        default=ActiveDefenseType.KICK,
        description="Active defense strategy to execute"
    )
    duration: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Maximum operation duration in seconds"
    )
    intensity: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Operation intensity (1=minimal, 10=maximum)"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "type": "arp_flood",
                "duration": 120,
                "intensity": 5
            }
        }
    )


class ActiveDefenseResponse(BaseModel):
    """Response for active defense operations.
    
    Attributes:
        device_mac: Target device MAC address
        status: Current operation status
        message: Status or error message
        start_time: Operation start timestamp (ISO format)
    """

    device_mac: str = Field(..., description="Target device MAC address")
    status: ActiveDefenseStatus = Field(..., description="Operation status")
    message: str | None = Field(None, description="Status or error message")
    start_time: str | None = Field(None, description="Operation start time (ISO 8601)")

    model_config = ConfigDict(from_attributes=True)


# Legacy aliases for backward compatibility (will be deprecated)
AttackType = ActiveDefenseType
AttackStatus = ActiveDefenseStatus
AttackRequest = ActiveDefenseRequest
AttackResponse = ActiveDefenseResponse
