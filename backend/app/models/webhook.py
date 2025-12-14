"""Webhook event models and verification helpers.

Defines typed payloads for incoming integration webhooks and utilities for
signature header names.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class WebhookEventType(str, Enum):
    DEVICE_ONLINE = "device.online"
    POLICY_SWITCHED = "policy.switched"


class WebhookBase(BaseModel):
    """Base fields for all webhook events."""

    id: str = Field(..., description="Event ID (producer assigned)")
    type: WebhookEventType = Field(..., description="Event type")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Event time (UTC)"
    )

    model_config = ConfigDict(from_attributes=True)


class DeviceOnlinePayload(BaseModel):
    mac: str = Field(..., description="Device MAC")
    ip: str | None = Field(None, description="Device IPv4/IPv6 if known")
    vendor: str | None = Field(None, description="OUI/vendor if available")


class DeviceOnlineEvent(WebhookBase):
    data: DeviceOnlinePayload


class PolicySwitchedPayload(BaseModel):
    mac: str = Field(..., description="Target MAC")
    from_policy: str | None = Field(None, description="Previous policy name")
    to_policy: str = Field(..., description="New policy name")
    reason: str | None = Field(None, description="Why switched")


class PolicySwitchedEvent(WebhookBase):
    data: PolicySwitchedPayload


# Header names for signature verification
HEADER_TIMESTAMP = "X-ZH-Timestamp"
HEADER_SIGNATURE = "X-ZH-Signature"  # format: sha256=<hex>
