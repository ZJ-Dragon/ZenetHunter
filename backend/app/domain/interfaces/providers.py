"""Repository-local provider contracts for replaceable low-level capabilities."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol


@dataclass(slots=True)
class CapabilityState:
    """Normalized availability state for a low-level capability."""

    name: str
    available: bool
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CapabilityReport:
    """Repository-local summary of runtime low-level capabilities."""

    platform: str
    platform_name: str
    is_root: bool
    capabilities: dict[str, CapabilityState]


@dataclass(slots=True)
class DiscoveryRequest:
    """Input to discovery providers."""

    target_subnets: list[str] | None = None
    scan_run_id: str | None = None


@dataclass(slots=True)
class DiscoveredDevice:
    """Normalized discovery output passed to probe/extraction stages."""

    ip: str
    mac: str | None
    interface: str | None
    source: str
    last_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProbeObservation:
    """Normalized probe output used by fingerprint extraction and persistence."""

    protocol: str
    key_fields: dict[str, Any]
    raw_fields: dict[str, Any]
    summary: str | None = None
    evidence_sources: list[str] = field(default_factory=list)


class DiscoveryProvider(Protocol):
    """Find candidate or confirmed devices on the local network."""

    name: str

    async def discover(self, request: DiscoveryRequest) -> list[DiscoveredDevice]:
        """Return discovered devices for the requested scan scope."""


class ProbeProvider(Protocol):
    """Collect lightweight probe observations for a discovered device."""

    name: str

    async def probe(self, device: DiscoveredDevice) -> list[ProbeObservation]:
        """Return probe observations for a discovered device."""


class FingerprintExtractor(Protocol):
    """Extract stable fingerprint data from probe observations."""

    name: str

    def extract(
        self,
        device: DiscoveredDevice,
        observations: Sequence[ProbeObservation],
    ) -> dict[str, Any]:
        """Build a normalized fingerprint payload for recognition and matching."""


class DefenseExecutor(Protocol):
    """Execute or simulate low-level defense operations for the upper layers."""

    name: str

    def get_capability(self) -> CapabilityState:
        """Report whether this executor is actually usable and why."""

    async def start(self, target_mac: str, operation_type: str, duration: int) -> None:
        """Start a low-level defense operation."""

    async def stop(self, target_mac: str) -> None:
        """Stop a low-level defense operation."""


class CapabilityProvider(Protocol):
    """Provide a coherent capability report for backend consumers."""

    def get_report(self) -> CapabilityReport:
        """Return the current normalized capability report."""
