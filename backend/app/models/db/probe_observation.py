"""Probe observation ORM model for scan/probe telemetry."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProbeObservationModel(Base):
    """Persisted observation captured during probe/enrichment stages."""

    __tablename__ = "probe_observations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    device_mac: Mapped[str] = mapped_column(String(17), index=True, nullable=False)
    scan_run_id: Mapped[str] = mapped_column(String(36), index=True, nullable=True)
    protocol: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    key_fields: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    keywords: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    keyword_hits: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    raw_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    redaction_level: Mapped[str] = mapped_column(
        String(32), nullable=False, default="standard"
    )
