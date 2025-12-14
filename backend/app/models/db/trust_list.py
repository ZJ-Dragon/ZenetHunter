"""Trust list ORM model (allow/block lists)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TrustListTypeEnum(str, Enum):
    """Trust list type enumeration."""

    ALLOW = "allow"
    BLOCK = "block"


class TrustListModel(Base):
    """Trust list ORM model for allow/block lists."""

    __tablename__ = "trust_list"

    # Primary key: auto-increment ID
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # MAC address (normalized to lowercase)
    mac: Mapped[str] = mapped_column(String(17), nullable=False, index=True)
    # List type: allow or block
    list_type: Mapped[TrustListTypeEnum] = mapped_column(
        SQLEnum(TrustListTypeEnum), nullable=False, index=True
    )
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    # Optional notes
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Unique constraint: same MAC cannot be in both lists
    __table_args__ = (
        UniqueConstraint("mac", "list_type", name="uq_trust_list_mac_type"),
    )
