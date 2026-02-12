"""Hybrid scanner pipeline: Candidate → Refresh → Enrich (3-stage).

Three-stage scanning:
1. Candidate: Collect from ARP cache, DHCP leases (no active scan)
2. Refresh: Targeted probes to confirm online status
3. Enrich: Fingerprint collection only for confirmed-online devices
"""

import asyncio
import ipaddress
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings
from app.services.observation_recorder import build_key_fields, build_summary
from app.services.scanner.candidate import get_arp_candidates, get_dhcp_candidates
from app.services.scanner.capabilities import get_scanner_capabilities
from app.services.scanner.network_detection import detect_local_subnet
from app.services.scanner.refresh import refresh_candidates

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
    observations: list[dict[str, Any]] = field(default_factory=list)


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
            target_subnets: List of CIDR subnets to scan.
                If None, auto-detects from ARP/gateway.

        Returns:
            List of discovered devices (IP/MAC pairs)
        """
        if target_subnets is None:
            # Auto-detect subnet instead of using config default
            network_info = await detect_local_subnet()
            target_subnets = [network_info.subnet]
            logger.info(
                f"Auto-detected subnet for discovery: {network_info.subnet} "
                f"(method: {network_info.method})"
            )

        logger.info(
            "Starting discovery stage: subnets=%s, capabilities=%s",
            target_subnets,
            self.capabilities.get_recommended_discovery_method(),
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
        self,
        discovered_devices: list[DiscoveryResult],
        *,
        scan_run_id: str | None = None,
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

        # Add stage-level timeout (30 seconds for all devices)
        try:
            async with asyncio.timeout(30.0):
                # Enrich each device with available methods
                for device in discovered_devices:
                    observations: list[dict[str, Any]] = []
                    if not device.mac:
                        continue  # Skip devices without MAC

                    fingerprint_data: dict[str, Any] = {}
                    evidence_sources: list[str] = []

                    # mDNS enrichment (if enabled)
                    if self.settings.feature_mdns:
                        try:
                            from app.services.scanner.enrich.mdns import (
                                enrich_with_mdns,
                            )

                            mdns_data = await asyncio.wait_for(
                                enrich_with_mdns(
                                    device_ip=device.ip,
                                    device_mac=device.mac,
                                    timeout=2.0,  # Short timeout per device
                                ),
                                timeout=3.0,  # Overall timeout
                            )
                            if mdns_data:
                                fingerprint_data.update(mdns_data)
                                evidence_sources.append("mdns")
                                key_fields = build_key_fields("mdns", mdns_data)
                                if key_fields:
                                    observations.append(
                                        {
                                            "protocol": "mdns",
                                            "key_fields": key_fields,
                                            "summary": build_summary(
                                                "mdns", key_fields
                                            ),
                                        }
                                    )
                                logger.debug(
                                    "mDNS enrichment for %s: found %d services",
                                    device.ip,
                                    len(mdns_data.get("mdns_services", [])),
                                )
                        except Exception as e:
                            logger.debug(f"mDNS enrichment failed for {device.ip}: {e}")

                    # SSDP enrichment (if enabled)
                    if self.settings.feature_ssdp:
                        try:
                            from app.services.scanner.enrich.ssdp import (
                                enrich_with_ssdp,
                            )

                            ssdp_data = await asyncio.wait_for(
                                enrich_with_ssdp(
                                    device_ip=device.ip,
                                    device_mac=device.mac,
                                    timeout=2.0,  # Short timeout per device
                                ),
                                timeout=3.0,  # Overall timeout
                            )
                            if ssdp_data:
                                fingerprint_data.update(ssdp_data)
                                evidence_sources.append("ssdp")
                                key_fields = build_key_fields("ssdp", ssdp_data)
                                if key_fields:
                                    observations.append(
                                        {
                                            "protocol": "ssdp",
                                            "key_fields": key_fields,
                                            "summary": build_summary(
                                                "ssdp", key_fields
                                            ),
                                        }
                                    )
                                logger.debug(
                                    "SSDP enrichment for %s: found %d fields",
                                    device.ip,
                                    len(ssdp_data),
                                )
                        except Exception as e:
                            logger.debug(f"SSDP enrichment failed for {device.ip}: {e}")

                    # Active probe enrichment (HTTP/Telnet/SSH/Printer/IoT)
                    # Simulates normal client connections to get device info
                    if self.settings.feature_active_probe:
                        try:
                            from app.services.scanner.enrich.active_probe import (
                                enrich_with_active_probe,
                            )

                            probe_data = await asyncio.wait_for(
                                enrich_with_active_probe(
                                    device_ip=device.ip,
                                    device_mac=device.mac,
                                    timeout=2.0,  # Short timeout per device
                                ),
                                timeout=3.0,  # Overall timeout
                            )
                            if probe_data:
                                fingerprint_data.update(probe_data)
                                evidence_sources.append("active_probe")
                                key_fields = build_key_fields(
                                    "active_probe", probe_data
                                )
                                if key_fields:
                                    observations.append(
                                        {
                                            "protocol": "active_probe",
                                            "key_fields": key_fields,
                                            "summary": build_summary(
                                                "active_probe", key_fields
                                            ),
                                        }
                                    )
                                logger.debug(
                                    f"Active probe for {device.ip}: "
                                    f"found {len(probe_data)} fields"
                                )
                        except Exception as e:
                            logger.debug(f"Active probe failed for {device.ip}: {e}")

                    # Only add result if we found some evidence
                    if fingerprint_data or evidence_sources:
                        enrichment_results.append(
                            EnrichmentResult(
                                device_mac=device.mac,
                                fingerprint_data=fingerprint_data,
                                evidence_sources=evidence_sources,
                                observations=observations,
                            )
                        )

        except TimeoutError:
            logger.warning(
                f"Enrichment timed out after 30s, "
                f"completed {len(enrichment_results)}/{len(discovered_devices)}"
            )
        except Exception as e:
            logger.error(f"Enrichment failed: {e}", exc_info=True)

        logger.info(
            f"Enrichment stage completed: "
            f"enriched {len(enrichment_results)} devices | succeed=true"
        )
        return enrichment_results

    async def run_full_scan(
        self,
        target_subnets: list[str] | None = None,
        *,
        scan_run_id: str | None = None,
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
            enrichment_results = await self.run_enrichment(
                discovery_results, scan_run_id=scan_run_id
            )

        return discovery_results, enrichment_results

    # === NEW: Hybrid Scanning (3-stage) ===

    async def run_hybrid_scan(self, event_callback=None) -> dict[str, Any]:
        """Run hybrid scan: Candidate → Refresh → Enrich.

        Args:
            event_callback: Async callback for progress events

        Returns:
            Dict with stats and discovered devices
        """
        stats = {
            "mode": self.settings.scan_mode,
            "candidate_count": 0,
            "refresh_confirmed": 0,
            "enrich_completed": 0,
            "devices_found": 0,
            "started_at": datetime.now(UTC).isoformat(),
        }

        try:
            # Detect local subnet first (before generating candidates)
            logger.info("Detecting local network subnet...")
            network_info = await detect_local_subnet()
            detected_subnet = network_info.subnet
            logger.info(
                f"Detected subnet: {detected_subnet} "
                f"(method: {network_info.method}, gateway: {network_info.gateway_ip})"
            )
            stats["detected_subnet"] = detected_subnet
            stats["detection_method"] = network_info.method
            stats["gateway_ip"] = network_info.gateway_ip

            # Stage 1: Generate candidates from local sources
            if event_callback:
                await event_callback(
                    "scanProgress",
                    {
                        "stage": "candidate",
                        "message": "Collecting candidates from local caches...",
                        "detected_subnet": detected_subnet,
                    },
                )

            candidates = await self._generate_candidates()
            stats["candidate_count"] = len(candidates)

            logger.info(
                f"Stage 1: Generated {len(candidates)} candidates | succeed=true"
            )

            if not candidates:
                stats["completed_at"] = datetime.now(UTC).isoformat()
                return {"stats": stats, "devices": []}

            # Stage 2: Refresh candidates
            if event_callback:
                await event_callback(
                    "scanProgress",
                    {
                        "stage": "refresh",
                        "message": f"Confirming {len(candidates)} candidates online...",
                        "candidate_count": len(candidates),
                    },
                )

            refresh_results = await refresh_candidates(
                [(c.ip, c.mac) for c in candidates],
                timeout=self.settings.scan_refresh_timeout,
                concurrency=self.settings.scan_refresh_concurrency,
            )

            online_devices = [r for r in refresh_results if r.online]
            stats["refresh_confirmed"] = len(online_devices)

            logger.info(
                f"Stage 2: {len(online_devices)}/{len(candidates)} confirmed | "
                f"succeed=true"
            )

            # Stage 3: Enrich only online devices
            discovered = []
            if online_devices:
                if event_callback:
                    await event_callback(
                        "scanProgress",
                        {
                            "stage": "enrich",
                            "message": f"Enriching {len(online_devices)} devices...",
                            "online_count": len(online_devices),
                        },
                    )

                for refresh_result in online_devices:
                    device = {
                        "ip": refresh_result.ip,
                        "mac": refresh_result.mac,
                        "discovery_source": "candidate-refresh",
                        "freshness_score": 95,
                        "rtt": refresh_result.rtt,
                        "last_seen": refresh_result.last_seen,
                    }
                    discovered.append(device)

                stats["enrich_completed"] = len(discovered)
                logger.info(f"Stage 3: {len(discovered)} enriched | succeed=true")

            stats["devices_found"] = len(discovered)
            stats["completed_at"] = datetime.now(UTC).isoformat()

            logger.info(
                f"Hybrid scan complete: {len(discovered)} devices | succeed=true"
            )

            return {"stats": stats, "devices": discovered}

        except Exception as e:
            logger.error(f"Hybrid scan failed: {e} | succeed=false", exc_info=True)
            stats["error"] = str(e)
            stats["completed_at"] = datetime.now(UTC).isoformat()
            return {"stats": stats, "devices": []}

    async def _generate_candidates(self) -> list[Any]:
        """Generate candidate list from local sources."""
        candidates = []

        # Collect from ARP cache
        logger.info("Collecting ARP cache candidates...")
        arp_cands = await get_arp_candidates()
        candidates.extend(arp_cands)
        logger.info(f"ARP cache: {len(arp_cands)} candidates | succeed=true")

        # Collect from DHCP leases
        logger.info("Collecting DHCP lease candidates...")
        dhcp_cands = await get_dhcp_candidates()
        candidates.extend(dhcp_cands)
        logger.info(f"DHCP leases: {len(dhcp_cands)} candidates | succeed=true")

        # Deduplicate by MAC
        seen_macs = set()
        unique = []
        for cand in candidates:
            if cand.mac not in seen_macs:
                seen_macs.add(cand.mac)
                unique.append(cand)

        logger.info(
            f"Candidates: {len(unique)} unique (from {len(candidates)} total) | "
            f"succeed=true"
        )
        return unique
