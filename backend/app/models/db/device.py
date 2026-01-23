"""Device ORM model."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.attack import ActiveDefenseStatus

if TYPE_CHECKING:
    from app.models.db.device_fingerprint import DeviceFingerprintModel


class DeviceTypeEnum(str, Enum):
    """Device type enumeration."""

    UNKNOWN = "unknown"
    ROUTER = "router"
    PC = "pc"
    MOBILE = "mobile"
    IOT = "iot"


class DeviceStatusEnum(str, Enum):
    """Device status enumeration."""

    ONLINE = "online"
    OFFLINE = "offline"
    BLOCKED = "blocked"


class DeviceModel(Base):
    """Device ORM model for database persistence."""

    __tablename__ = "devices"

    # Primary key: MAC address (normalized to lowercase)
    mac: Mapped[str] = mapped_column(String(17), primary_key=True, index=True)
    # IP address (stored as string to support IPv4/IPv6)
    ip: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    # Device name/alias
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Vendor (from MAC OUI lookup)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Device model (from MAC address lookup)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Device type
    type: Mapped[DeviceTypeEnum] = mapped_column(
        SQLEnum(DeviceTypeEnum), default=DeviceTypeEnum.UNKNOWN, nullable=False
    )
    # Connection status
    status: Mapped[DeviceStatusEnum] = mapped_column(
        SQLEnum(DeviceStatusEnum), default=DeviceStatusEnum.ONLINE, nullable=False
    )
    # Active defense operation status
    active_defense_status: Mapped[ActiveDefenseStatus] = mapped_column(
        SQLEnum(ActiveDefenseStatus), default=ActiveDefenseStatus.IDLE, nullable=False
    )
    # Timestamps
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    # Additional metadata (JSON stored as text)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of tags
    alias: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # User-friendly alias
    # Recognition fields (denormalized from fingerprint for quick access)
    vendor_guess: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_guess: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recognition_confidence: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 0-100
    recognition_evidence: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON
    recognition_manual_override: Mapped[bool] = mapped_column(
        default=False, nullable=False, server_default="0"
    )  # Admin manually confirmed recognition

    # Scanning metadata (hybrid scanner)
    discovery_source: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # candidate-cache, dhcp, active-refresh, enrich, full-scan
    freshness_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 0-100: how fresh/reliable is this data

    # Relationship to fingerprint (optional)
    fingerprint: Mapped[DeviceFingerprintModel | None] = relationship(
        "DeviceFingerprintModel",
        back_populates="device",
        uselist=False,
        cascade="all, delete-orphan",
    )
