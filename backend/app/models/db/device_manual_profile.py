"""Device manual profile ORM model.

Stores long-lived manual labels and matching hints so they survive device resets.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DeviceManualProfileModel(Base):
    """Manual profile for devices (persistent, matchable)."""

    __tablename__ = "device_manual_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    manual_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manual_vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fingerprint_key: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True, unique=True
    )
    match_keys: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    mac: Mapped[str | None] = mapped_column(String(17), nullable=True, index=True)
    ip_hint: Mapped[str | None] = mapped_column(String(45), nullable=True)
    keywords: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
