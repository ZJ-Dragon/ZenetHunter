"""Unified runtime capability provider."""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.core.platform.detect import get_platform_features
from app.domain.interfaces.providers import (
    CapabilityProvider,
    CapabilityReport,
    CapabilityState,
)
from app.providers.defense import get_defense_executor
from app.services.scanner.capabilities import get_scanner_capabilities


class RuntimeCapabilityProvider(CapabilityProvider):
    """Coherent low-level capability report for backend consumers."""

    def get_report(self) -> CapabilityReport:
        platform_features = get_platform_features()
        scanner_capabilities = get_scanner_capabilities()
        defense_executor = get_defense_executor()
        settings = get_settings()

        capabilities = {
            "root_permissions": CapabilityState(
                name="root_permissions",
                available=platform_features.is_root,
                reason=(
                    None
                    if platform_features.is_root
                    else "Process is not running with elevated privileges"
                ),
            ),
            "scapy_import": CapabilityState(
                name="scapy_import",
                available=platform_features.has_scapy,
                reason=None if platform_features.has_scapy else "Scapy import failed",
            ),
            "arp_sweep": CapabilityState(
                name="arp_sweep",
                available=scanner_capabilities.can_arp_sweep(),
                reason=(
                    None
                    if scanner_capabilities.can_arp_sweep()
                    else scanner_capabilities.reason
                ),
            ),
            "icmp_ping": CapabilityState(
                name="icmp_ping",
                available=scanner_capabilities.can_icmp_ping(),
                reason=(
                    None
                    if scanner_capabilities.can_icmp_ping()
                    else "ICMP probing is not available on this runtime"
                ),
            ),
            "tcp_probe": CapabilityState(
                name="tcp_probe",
                available=scanner_capabilities.can_tcp_probe(),
            ),
            "mdns": CapabilityState(
                name="mdns",
                available=scanner_capabilities.can_mdns(),
                metadata={"feature_enabled": settings.feature_mdns},
            ),
            "ssdp": CapabilityState(
                name="ssdp",
                available=scanner_capabilities.can_ssdp(),
                metadata={"feature_enabled": settings.feature_ssdp},
            ),
            "nbns": CapabilityState(
                name="nbns",
                available=scanner_capabilities.can_nbns(),
                reason=(
                    None
                    if scanner_capabilities.can_nbns()
                    else "NBNS probing is disabled or unsupported on this platform"
                ),
                metadata={"feature_enabled": settings.feature_nbns},
            ),
            "snmp": CapabilityState(
                name="snmp",
                available=scanner_capabilities.can_snmp(),
                reason=(
                    None
                    if scanner_capabilities.can_snmp()
                    else "SNMP probing requires additional configuration"
                ),
                metadata={"feature_enabled": settings.feature_snmp},
            ),
            "active_probe": CapabilityState(
                name="active_probe",
                available=settings.feature_active_probe,
                reason=(
                    None
                    if settings.feature_active_probe
                    else "Active probe enrichment is disabled by configuration"
                ),
            ),
            "defense_executor": defense_executor.get_capability(),
        }

        return CapabilityReport(
            platform=platform_features.platform.value,
            platform_name=platform_features.get_summary()["platform_name"],
            is_root=platform_features.is_root,
            capabilities=capabilities,
        )


def serialize_capability_report(report: CapabilityReport) -> dict[str, Any]:
    """Convert a capability report into JSON-serializable response data."""
    serialized: dict[str, Any] = {
        "platform": report.platform,
        "platform_name": report.platform_name,
        "is_root": report.is_root,
        "capabilities": {},
    }
    for name, capability in report.capabilities.items():
        serialized["capabilities"][name] = {
            "available": capability.available,
            "reason": capability.reason,
            "metadata": capability.metadata,
        }
    return serialized


_provider_instance: RuntimeCapabilityProvider | None = None


def get_runtime_capability_provider() -> RuntimeCapabilityProvider:
    """Return the singleton runtime capability provider."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = RuntimeCapabilityProvider()
    return _provider_instance
