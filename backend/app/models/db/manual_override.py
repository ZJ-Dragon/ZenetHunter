"""Manual Override ORM model for fingerprint-based device labeling.

This table stores user-provided device names and vendors that can be
automatically applied to devices with matching fingerprints.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ManualOverrideModel(Base):
    """Manual Override model for storing user-provided device labels.

    When a user manually labels a device's name or vendor, the fingerprint
    characteristics are normalized into a stable 'fingerprint_key'. If another
    device appears with the same fingerprint_key, the manual labels can be
    automatically applied.
    """

    __tablename__ = "manual_overrides"

    # Primary key: auto-increment ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Fingerprint key: normalized hash of device fingerprint characteristics
    # This allows matching across different MAC addresses with same fingerprint
    fingerprint_key: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, unique=True
    )

    # Manual labels provided by user
    manual_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manual_vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Source device information (for audit/reference)
    source_mac: Mapped[str | None] = mapped_column(
        String(17), nullable=True
    )  # MAC of device that created this override
    source_ip: Mapped[str | None] = mapped_column(
        String(45), nullable=True
    )  # IP at time of override

    # Fingerprint components used to generate the key (for debugging/audit)
    fingerprint_components: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON: what signals were used

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    created_by: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Username who created
    updated_by: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Username who last updated

    # Match count: how many devices have been auto-labeled using this override
    match_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
