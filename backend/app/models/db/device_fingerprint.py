"""Device fingerprint ORM model for multi-signal device recognition."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.db.device import DeviceModel


class DeviceFingerprintModel(Base):
    """Device fingerprint ORM model for storing recognition signals."""

    __tablename__ = "device_fingerprints"

    # Primary key: device MAC (foreign key to devices table)
    device_mac: Mapped[str] = mapped_column(
        String(17),
        ForeignKey("devices.mac", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    # DHCP Option 12: Host Name
    dhcp_opt12_hostname: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    # DHCP Option 55: Parameter Request List (comma-separated ints or JSON)
    dhcp_opt55_prl: Mapped[str | None] = mapped_column(Text, nullable=True)
    # DHCP Option 60: Vendor Class Identifier
    dhcp_opt60_vci: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    # User Agent (from HTTP/HTTPS traffic)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    # mDNS services (JSON array)
    mdns_services: Mapped[str | None] = mapped_column(Text, nullable=True)
    # SSDP server header (JSON array)
    ssdp_server: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JA3 TLS fingerprint
    ja3: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # Recognition results
    best_guess_vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    best_guess_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 0-100 confidence score
    # Evidence (JSON: matched fields, weights, sources)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Timestamps
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationship to device (optional, for convenience)
    device: Mapped[DeviceModel] = relationship(
        "DeviceModel", back_populates="fingerprint"
    )
