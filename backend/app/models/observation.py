"""Observation schemas for probe telemetry."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProbeObservation(BaseModel):
    """Normalized observation record."""

    id: str = Field(..., description="Observation ID (UUID string)")
    device_mac: str = Field(..., description="Associated device MAC")
    scan_run_id: str | None = Field(
        None, description="Scan run identifier that produced this observation"
    )
    protocol: str = Field(..., description="Probe protocol/module name")
    timestamp: datetime = Field(..., description="When the observation was recorded")
    key_fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured key fields extracted from probe response",
    )
    keywords: list[str] = Field(
        default_factory=list, description="Keywords derived from key_fields"
    )
    keyword_hits: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Applied dictionary rules and matched tokens "
            "(rule_id, matched_token, infer/infer_summary, confidence_delta, notes)"
        ),
    )
    raw_summary: str | None = Field(
        None, description="Short summary of the observation (no raw payload)"
    )
    redaction_level: str = Field(
        default="standard",
        description="Redaction level applied to the observation",
    )

    model_config = ConfigDict(from_attributes=True)


class ProbeObservationList(BaseModel):
    """Envelope for observation lists."""

    items: list[ProbeObservation]
    total: int
