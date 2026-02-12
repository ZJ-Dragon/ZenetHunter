"""Manual profile schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DeviceManualProfile(BaseModel):
    """Persistent manual profile used to override device identity."""

    id: int
    manual_name: str | None = Field(None, description="Manual device name")
    manual_vendor: str | None = Field(None, description="Manual vendor name")
    fingerprint_key: str | None = Field(None, description="Stable fingerprint key")
    match_keys: dict[str, Any] = Field(
        default_factory=dict, description="Matching hints (normalized values)"
    )
    mac: str | None = Field(None, description="Exact MAC match (optional)")
    ip_hint: str | None = Field(None, description="Optional IP hint (weak)")
    keywords: list[str] = Field(
        default_factory=list, description="Optional keywords for debugging"
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
