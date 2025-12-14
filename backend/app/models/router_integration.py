from __future__ import annotations

"""Models for router integration (rate limit, ACL, guest isolation).

This module defines the stable data contracts used by the Router abstraction
layer and the REST API endpoints under /api/integration/router.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ActionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class Protocol(str, Enum):
    ANY = "any"
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"


class ACLAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


class RateLimitPolicy(BaseModel):
    """Per-device rate limit policy.

    Units are in kbps to avoid floats, and directions are explicit.
    """

    target_mac: str = Field(..., description="Target device MAC")
    up_kbps: int | None = Field(
        None, ge=0, description="Uplink limit in kbps (None = unlimited)"
    )
    down_kbps: int | None = Field(
        None, ge=0, description="Downlink limit in kbps (None = unlimited)"
    )
    duration: int | None = Field(
        None, ge=1, le=7 * 24 * 3600, description="Auto-revert after seconds"
    )

    @model_validator(mode="after")
    def _validate_directions(self) -> "RateLimitPolicy":
        if self.up_kbps is None and self.down_kbps is None:
            raise ValueError("At least one of up_kbps or down_kbps must be set")
        return self

    model_config = ConfigDict(from_attributes=True)


class ACLRule(BaseModel):
    """Simplified ACL rule model.

    - src/dst accept CIDR or "any".
    - proto supports any/tcp/udp/icmp.
    - port: a single port (e.g., "80") or range (e.g., "1000-2000"); optional.
    """

    rule_id: str | None = Field(
        None, description="Stable rule identifier (if known on deletion)"
    )
    src: str = Field("any", description="Source CIDR or 'any'")
    dst: str = Field("any", description="Destination CIDR or 'any'")
    proto: Protocol = Field(Protocol.ANY, description="L4 protocol")
    port: str | None = Field(
        None, description="Single port or range 'start-end' (None = any)"
    )
    action: ACLAction = Field(..., description="allow or deny")
    priority: int = Field(100, ge=0, le=65535, description="Rule priority")
    comment: str | None = Field(None, description="Human note for the rule")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("port")
    @classmethod
    def _validate_port(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v.isdigit():
            # single port
            return v
        if "-" in v:
            start, _, end = v.partition("-")
            if start.isdigit() and end.isdigit() and int(start) <= int(end):
                return v
        raise ValueError("port must be a number or 'start-end'")


class IsolationMode(str, Enum):
    GUEST_VLAN = "guest_vlan"
    SSID = "ssid"
    ROUTER = "router"


class IsolationPolicy(BaseModel):
    """Guest isolation policy.

    Mode-specific parameters:
    - guest_vlan: requires vlan_id
    - ssid: requires ssid
    - router: no extra fields (router-side isolation only)
    """

    target_mac: str = Field(..., description="Target device MAC")
    mode: IsolationMode = Field(
        default=IsolationMode.GUEST_VLAN, description="Isolation mode"
    )
    vlan_id: int | None = Field(None, ge=1, le=4094)
    ssid: str | None = None
    duration: int | None = Field(
        None, ge=1, le=7 * 24 * 3600, description="Auto-revert after seconds"
    )

    @model_validator(mode="after")
    def _validate_mode(self) -> "IsolationPolicy":
        if self.mode == IsolationMode.GUEST_VLAN and self.vlan_id is None:
            raise ValueError("vlan_id is required for guest_vlan mode")
        if self.mode == IsolationMode.SSID and not self.ssid:
            raise ValueError("ssid is required for ssid mode")
        return self

    model_config = ConfigDict(from_attributes=True)


class RouterActionResult(BaseModel):
    status: ActionStatus = Field(..., description="Result status")
    message: str | None = Field(None, description="Optional message")
    data: dict[str, str | int | bool] | None = Field(
        None, description="Optional structured data (e.g., rule_id)"
    )

    model_config = ConfigDict(from_attributes=True)
