"""Event log ORM model for audit and system events."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import DateTime, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EventLogLevelEnum(str, Enum):
    """Event log level enumeration."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventLogModel(Base):
    """Event log ORM model for system events and audit logs."""

    __tablename__ = "event_log"

    # Primary key: auto-increment ID
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    # Log level
    level: Mapped[EventLogLevelEnum] = mapped_column(
        SQLEnum(EventLogLevelEnum), nullable=False, index=True
    )
    # Module/component
    module: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Event message
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # Correlation ID (for request tracing)
    correlation_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    # Device MAC (if event is device-related)
    device_mac: Mapped[str | None] = mapped_column(
        String(17), nullable=True, index=True
    )
    # Additional context (JSON stored as text)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON object
