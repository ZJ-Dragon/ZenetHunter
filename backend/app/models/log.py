from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SystemLog(BaseModel):
    """System log entry model."""

    id: UUID | None = Field(default=None, description="Unique log ID (from DB)")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Log timestamp"
    )
    level: str = Field(..., description="Log severity level (debug/info/warning/error/critical)")
    module: str = Field(..., description="Source module/component")
    message: str = Field(..., description="Log message")
    correlation_id: str | None = Field(default=None, description="Request correlation ID")
    device_mac: str | None = Field(default=None, description="Device MAC if device-related")
    context: dict[str, Any] | None = Field(
        default=None, description="Additional context data (JSON)"
    )

    model_config = ConfigDict(from_attributes=True)
