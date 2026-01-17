"""Active probe scanner pipeline (Stage A: Discovery, Stage B: Enrichment)."""

import ipaddress
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings
from app.services.scanner.capabilities import get_scanner_capabilities

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryResult:
    """Result from Stage A: Device discovery."""

    ip: str
    mac: str | None
    interface: str
    partial: bool = False  # True if MAC is missing
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)


@dataclass
class EnrichmentResult:
    """Result from Stage B: Fingerprint enrichment."""

    device_mac: str
    fingerprint_data: dict[str, Any]
    evidence_sources: list[str]


class ScanPipeline:
    """
    Active probe scanning pipeline.

    Stage A: Discovery - Find online devices (ARP/ICMP/TCP)
    Stage B: Enrichment - Gather fingerprint evidence (mDNS/SSDP/etc.)
    """

    def __init__(self):
        self.capabilities = get_scanner_capabilities()
        self.settings = get_settings()

    async def run_discovery(
        self, target_subnets: list[str] | None = None
    ) -> list[DiscoveryResult]:
        """
        Stage A: Discover online devices using active probing.

        Args:
            target_subnets: List of CIDR subnets to scan. If None, uses config.

        Returns:
            List of discovered devices (IP/MAC pairs)
        """
        if target_subnets is None:
            target_subnets = [self.settings.scan_range]

        logger.info(
            f"Starting discovery stage: "
            f"subnets={target_subnets}, "
            f"capabilities={self.capabilities.get_recommended_discovery_method()}"
        )

        all_results: list[DiscoveryResult] = []

        # Parse subnets and generate IP ranges
        ip_targets: list[str] = []
        for subnet_str in target_subnets:
            try:
                network = ipaddress.ip_network(subnet_str, strict=False)
                # Generate list of host IPs (exclude network/broadcast)
                for ip in network.hosts():
                    ip_targets.append(str(ip))
            except ValueError as e:
                logger.warning(f"Invalid subnet {subnet_str}: {e}")

        logger.info(
            f"Generated {len(ip_targets)} IP targets from {len(target_subnets)} subnets"
        )

        # Choose discovery method based on capabilities
        method = self.capabilities.get_recommended_discovery_method()

        if method == "arp_sweep" and self.capabilities.can_arp_sweep():
            # Use active ARP sweep
            from app.services.scanner.discovery.arp_sweep import ARPSweep

            logger.info("ARP sweep discovery selected")
            sweeper = ARPSweep(
                timeout=self.settings.scan_timeout_sec,
                concurrency=self.settings.scan_concurrency,
            )
            for subnet_str in target_subnets:
                sweep_results = await sweeper.sweep_subnet(subnet_str)
                # Convert to DiscoveryResult
                for ip, mac, interface in sweep_results:
                    all_results.append(
                        DiscoveryResult(
                            ip=ip, mac=mac, interface=interface, partial=(mac is None)
                        )
                    )
        elif method == "icmp_sweep" and self.capabilities.can_icmp_ping():
            # ICMP ping sweep will be implemented later
            logger.info("ICMP sweep discovery selected (implementation pending)")
            all_results = []
        else:
            # Fallback to TCP probe (non-privileged)
            logger.info("TCP probe discovery selected (non-privileged fallback)")
            # TCP probe will be implemented later
            all_results = []

        logger.info(f"Discovery stage completed: found {len(all_results)} devices")
        return all_results

    async def run_enrichment(
        self, discovered_devices: list[DiscoveryResult]
    ) -> list[EnrichmentResult]:
        """
        Stage B: Enrich device fingerprints using gentle probes.

        Args:
            discovered_devices: Devices discovered in Stage A

        Returns:
            List of enrichment results with fingerprint data
        """
        logger.info(
            f"Starting enrichment stage: {len(discovered_devices)} devices, "
            f"mDNS={self.settings.feature_mdns}, SSDP={self.settings.feature_ssdp}"
        )

        enrichment_results: list[EnrichmentResult] = []

        # Enrich each device with available methods
        for device in discovered_devices:
            if not device.mac:
                continue  # Skip devices without MAC

            fingerprint_data: dict[str, Any] = {}
            evidence_sources: list[str] = []

            # mDNS enrichment (if enabled)
            if self.settings.feature_mdns:
                try:
                    from app.services.scanner.enrich.mdns import enrich_with_mdns

                    mdns_data = await enrich_with_mdns(
                        device_ip=device.ip,
                        device_mac=device.mac,
                        timeout=self.settings.scan_timeout_sec,
                    )
                    if mdns_data:
                        fingerprint_data.update(mdns_data)
                        evidence_sources.append("mdns")
                        logger.debug(
                            f"mDNS enrichment for {device.ip}: "
                            f"found {len(mdns_data.get('mdns_services', []))} services"
                        )
                except Exception as e:
                    logger.debug(f"mDNS enrichment failed for {device.ip}: {e}")

            # SSDP enrichment (if enabled)
            if self.settings.feature_ssdp:
                try:
                    from app.services.scanner.enrich.ssdp import enrich_with_ssdp

                    ssdp_data = await enrich_with_ssdp(
                        device_ip=device.ip,
                        device_mac=device.mac,
                        timeout=self.settings.scan_timeout_sec,
                    )
                    if ssdp_data:
                        fingerprint_data.update(ssdp_data)
                        evidence_sources.append("ssdp")
                        logger.debug(
                            f"SSDP enrichment for {device.ip}: "
                            f"found {len(ssdp_data)} fields"
                        )
                except Exception as e:
                    logger.debug(f"SSDP enrichment failed for {device.ip}: {e}")

            # Only add result if we found some evidence
            if fingerprint_data or evidence_sources:
                enrichment_results.append(
                    EnrichmentResult(
                        device_mac=device.mac,
                        fingerprint_data=fingerprint_data,
                        evidence_sources=evidence_sources,
                    )
                )

        logger.info(
            f"Enrichment stage completed: "
            f"enriched {len(enrichment_results)} devices"
        )
        return enrichment_results

    async def run_full_scan(
        self, target_subnets: list[str] | None = None
    ) -> tuple[list[DiscoveryResult], list[EnrichmentResult]]:
        """
        Run complete scan pipeline: Stage A + Stage B.

        Args:
            target_subnets: List of CIDR subnets to scan

        Returns:
            Tuple of (discovery_results, enrichment_results)
        """
        # Stage A: Discovery
        discovery_results = await self.run_discovery(target_subnets)

        # Stage B: Enrichment (only if devices found)
        enrichment_results: list[EnrichmentResult] = []
        if discovery_results:
            enrichment_results = await self.run_enrichment(discovery_results)

        return discovery_results, enrichment_results
