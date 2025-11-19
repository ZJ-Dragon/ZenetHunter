from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SystemLog(BaseModel):
    """System log entry model."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique log ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Log timestamp")
    level: LogLevel = Field(..., description="Log severity level")
    module: str = Field(..., description="Source module/component")
    message: str = Field(..., description="Log message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional context data")

    class Config:
        from_attributes = True

