"""Application-layer capability reporting."""

from __future__ import annotations

from typing import Any

from app.domain.interfaces.providers import CapabilityProvider, CapabilityReport
from app.providers.capabilities import (
    get_runtime_capability_provider,
    serialize_capability_report,
)


class CapabilityReportingService:
    """Expose normalized capability data to API handlers."""

    def __init__(self, provider: CapabilityProvider | None = None):
        self.provider = provider or get_runtime_capability_provider()

    def get_report(self) -> CapabilityReport:
        return self.provider.get_report()

    def get_serialized_report(self) -> dict[str, Any]:
        return serialize_capability_report(self.get_report())


_service_instance: CapabilityReportingService | None = None


def get_capability_reporting_service() -> CapabilityReportingService:
    """Return the singleton capability reporting service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = CapabilityReportingService()
    return _service_instance
