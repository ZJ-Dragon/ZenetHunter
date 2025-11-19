from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SystemLog(BaseModel):
    """System log entry model."""

    id: UUID = Field(default_factory=uuid4, description="Unique log ID")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Log timestamp"
    )
    level: LogLevel = Field(..., description="Log severity level")
    module: str = Field(..., description="Source module/component")
    message: str = Field(..., description="Log message")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional context data"
    )

    model_config = ConfigDict(from_attributes=True)
