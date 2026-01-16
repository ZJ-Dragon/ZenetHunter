"""Fingerprint collector for gathering device recognition signals."""

import logging
from typing import Any

from app.services.fingerprint_normalizer import FingerprintNormalizer

logger = logging.getLogger(__name__)


class FingerprintCollector:
    """Collects device fingerprint signals from various sources."""

    def __init__(self):
        self.normalizer = FingerprintNormalizer()

    async def collect_from_device(
        self, device_ip: str, device_mac: str, device_name: str | None = None
    ) -> dict[str, Any]:
        """
        Collect fingerprint signals from available sources (non-privileged path).

        Currently extracts:
        - Hostname from device name (if available)
        - Future: DHCP options from lease files/logs
        - Future: mDNS/SSDP from network traffic

        Args:
            device_ip: Device IP address
            device_mac: Device MAC address
            device_name: Device hostname/name (if known)

        Returns:
            Dictionary with fingerprint fields (normalized)
        """
        fingerprint: dict[str, Any] = {}

        # Extract hostname from device name if available
        if device_name:
            fingerprint["dhcp_opt12_hostname"] = device_name

        # Normalize all collected fields
        normalized = self.normalizer.normalize_fingerprint(fingerprint)

        logger.debug(
            f"Collected fingerprint for {device_mac}: "
            f"hostname={normalized.get('dhcp_opt12_hostname')}"
        )

        return normalized

    async def collect_from_dhcp_lease(
        self, lease_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Extract fingerprint from DHCP lease data (future: read from lease files).

        Args:
            lease_data: Dictionary with DHCP lease information
                Expected keys: opt12_hostname, opt55_prl, opt60_vci

        Returns:
            Dictionary with normalized fingerprint fields
        """
        fingerprint: dict[str, Any] = {}

        # Extract DHCP options if present
        if "opt12_hostname" in lease_data:
            fingerprint["dhcp_opt12_hostname"] = lease_data["opt12_hostname"]
        if "opt55_prl" in lease_data:
            fingerprint["dhcp_opt55_prl"] = lease_data["opt55_prl"]
        if "opt60_vci" in lease_data:
            fingerprint["dhcp_opt60_vci"] = lease_data["opt60_vci"]

        # Normalize all fields
        normalized = self.normalizer.normalize_fingerprint(fingerprint)

        logger.debug(
            f"Collected DHCP fingerprint: "
            f"opt12={normalized.get('dhcp_opt12_hostname')}, "
            f"opt55={normalized.get('dhcp_opt55_prl')}, "
            f"opt60={normalized.get('dhcp_opt60_vci')}"
        )

        return normalized

    async def collect_from_network_traffic(
        self, traffic_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Extract fingerprint from network traffic (future: packet capture).

        Args:
            traffic_data: Dictionary with traffic information
                Expected keys: user_agent, ja3, mdns_services, ssdp_server

        Returns:
            Dictionary with normalized fingerprint fields
        """
        fingerprint: dict[str, Any] = {}

        # Extract optional signals
        if "user_agent" in traffic_data:
            fingerprint["user_agent"] = traffic_data["user_agent"]
        if "ja3" in traffic_data:
            fingerprint["ja3"] = traffic_data["ja3"]
        if "mdns_services" in traffic_data:
            fingerprint["mdns_services"] = traffic_data["mdns_services"]
        if "ssdp_server" in traffic_data:
            fingerprint["ssdp_server"] = traffic_data["ssdp_server"]

        # Normalize all fields
        normalized = self.normalizer.normalize_fingerprint(fingerprint)

        logger.debug(
            f"Collected traffic fingerprint: "
            f"ua={normalized.get('user_agent') is not None}, "
            f"ja3={normalized.get('ja3') is not None}"
        )

        return normalized

    async def merge_fingerprints(self, *fingerprints: dict[str, Any]) -> dict[str, Any]:
        """
        Merge multiple fingerprint dictionaries, with later ones overriding earlier.

        Args:
            *fingerprints: Variable number of fingerprint dictionaries

        Returns:
            Merged fingerprint dictionary (normalized)
        """
        merged: dict[str, Any] = {}

        for fp in fingerprints:
            if fp:
                merged.update(fp)

        # Normalize the merged result
        normalized = self.normalizer.normalize_fingerprint(merged)

        return normalized


# Global singleton instance
_collector_instance: FingerprintCollector | None = None


def get_fingerprint_collector() -> FingerprintCollector:
    """Get the global FingerprintCollector instance."""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = FingerprintCollector()
    return _collector_instance
