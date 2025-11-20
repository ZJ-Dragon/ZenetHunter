from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ScanStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanType(str, Enum):
    QUICK = "quick"  # ARP scan
    FULL = "full"  # ARP + Port scan
    PASSIVE = "passive"  # Sniffing only


class ScanRequest(BaseModel):
    """Request to start a network scan."""

    type: ScanType = Field(
        default=ScanType.QUICK, description="Type of scan to perform"
    )
    target_subnets: list[str] | None = Field(
        None,
        description=(
            "Specific subnets to scan (e.g. 192.168.1.0/24). If None, auto-detect."
        ),
    )

    model_config = ConfigDict(from_attributes=True)


class ScanResult(BaseModel):
    """Result of a scan operation."""

    id: UUID = Field(default_factory=uuid4, description="Unique scan ID")
    status: ScanStatus = Field(..., description="Final status of the scan")
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Start timestamp"
    )
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    devices_found: int = Field(0, description="Number of devices discovered")
    error: str | None = Field(None, description="Error message if failed")

    model_config = ConfigDict(from_attributes=True)
