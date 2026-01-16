"""Device ORM model."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import DateTime, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.attack import AttackStatus
from app.models.defender import DefenseStatus, DefenseType


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
    # Attack status
    attack_status: Mapped[AttackStatus] = mapped_column(
        SQLEnum(AttackStatus), default=AttackStatus.IDLE, nullable=False
    )
    # Defense status
    defense_status: Mapped[DefenseStatus] = mapped_column(
        SQLEnum(DefenseStatus), default=DefenseStatus.INACTIVE, nullable=False
    )
    # Active defense policy
    active_defense_policy: Mapped[DefenseType | None] = mapped_column(
        SQLEnum(DefenseType), nullable=True
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

    # Relationship to fingerprint (optional)
    fingerprint: Mapped["DeviceFingerprintModel | None"] = relationship(
        "DeviceFingerprintModel",
        back_populates="device",
        uselist=False,
        cascade="all, delete-orphan",
    )
