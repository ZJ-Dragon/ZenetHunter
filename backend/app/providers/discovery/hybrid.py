"""Hybrid discovery provider built from candidate refresh plus optional ARP sweep."""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.domain.interfaces.providers import (
    DiscoveredDevice,
    DiscoveryProvider,
    DiscoveryRequest,
)
from app.services.scanner.candidate import get_arp_candidates, get_dhcp_candidates
from app.services.scanner.capabilities import get_scanner_capabilities
from app.services.scanner.discovery.arp_sweep import ARPSweep
from app.services.scanner.refresh import refresh_candidates


class HybridDiscoveryProvider(DiscoveryProvider):
    """Prefer candidate refresh and fall back to active ARP sweep when possible."""

    name = "hybrid-discovery"

    def __init__(self):
        self.settings = get_settings()
        self.capabilities = get_scanner_capabilities()

    async def discover(self, request: DiscoveryRequest) -> list[DiscoveredDevice]:
        candidates = await self._collect_candidates()
        discovered = await self._discover_from_candidates(candidates)

        if discovered:
            return discovered

        if request.target_subnets and self.capabilities.can_arp_sweep():
            sweeper = ARPSweep(
                timeout=self.settings.scan_timeout_sec,
                concurrency=self.settings.scan_concurrency,
            )
            swept: list[DiscoveredDevice] = []
            for subnet in request.target_subnets:
                for ip, mac, interface in await sweeper.sweep_subnet(subnet):
                    if not mac:
                        continue
                    swept.append(
                        DiscoveredDevice(
                            ip=ip,
                            mac=mac,
                            interface=interface,
                            source="arp-sweep",
                            metadata={"freshness_score": 100},
                        )
                    )
            if swept:
                return _dedupe_discovered_devices(swept)

        return self._build_unconfirmed_candidates(candidates)

    async def _collect_candidates(self) -> dict[str, dict[str, Any]]:
        candidates: dict[str, dict[str, Any]] = {}

        for candidate in await get_arp_candidates():
            candidates[candidate.mac.lower()] = {
                "ip": candidate.ip,
                "mac": candidate.mac.lower(),
                "interface": candidate.interface,
                "source": candidate.source,
                "hostname": None,
            }

        for candidate in await get_dhcp_candidates():
            existing = candidates.get(candidate.mac.lower())
            payload = {
                "ip": candidate.ip,
                "mac": candidate.mac.lower(),
                "interface": existing["interface"] if existing else None,
                "source": candidate.source,
                "hostname": candidate.hostname,
            }
            if existing:
                payload["interface"] = existing["interface"]
                payload["source"] = existing["source"]
                payload["hostname"] = candidate.hostname or existing["hostname"]
            candidates[candidate.mac.lower()] = payload

        return candidates

    async def _discover_from_candidates(
        self, candidates: dict[str, dict[str, Any]]
    ) -> list[DiscoveredDevice]:
        if not candidates:
            return []

        refresh_results = await refresh_candidates(
            [(candidate["ip"], candidate["mac"]) for candidate in candidates.values()],
            timeout=self.settings.scan_refresh_timeout,
            concurrency=self.settings.scan_refresh_concurrency,
        )

        discovered: list[DiscoveredDevice] = []
        for result in refresh_results:
            if not result.online:
                continue
            candidate = candidates.get(result.mac.lower())
            metadata = {
                "freshness_score": 95,
                "rtt": result.rtt,
                "refresh_method": result.method,
            }
            if candidate and candidate.get("hostname"):
                metadata["hostname"] = candidate["hostname"]
            discovered.append(
                DiscoveredDevice(
                    ip=result.ip,
                    mac=result.mac.lower(),
                    interface=candidate["interface"] if candidate else None,
                    source="candidate-refresh",
                    last_seen=result.last_seen,
                    metadata=metadata,
                )
            )

        return _dedupe_discovered_devices(discovered)

    def _build_unconfirmed_candidates(
        self, candidates: dict[str, dict[str, Any]]
    ) -> list[DiscoveredDevice]:
        """Fallback to cached candidates when refresh cannot confirm them."""
        fallback: list[DiscoveredDevice] = []
        for candidate in candidates.values():
            metadata = {
                "freshness_score": 40,
                "refresh_state": "unconfirmed",
            }
            if candidate.get("hostname"):
                metadata["hostname"] = candidate["hostname"]
            fallback.append(
                DiscoveredDevice(
                    ip=candidate["ip"],
                    mac=candidate["mac"],
                    interface=candidate["interface"],
                    source=candidate["source"],
                    metadata=metadata,
                )
            )
        return _dedupe_discovered_devices(fallback)


def _dedupe_discovered_devices(
    discovered: list[DiscoveredDevice],
) -> list[DiscoveredDevice]:
    deduped: dict[str, DiscoveredDevice] = {}
    for device in discovered:
        key = (device.mac or device.ip).lower()
        current = deduped.get(key)
        if current is None:
            deduped[key] = device
            continue
        if current.metadata.get("hostname") or not device.metadata.get("hostname"):
            continue
        deduped[key] = device
    return list(deduped.values())


_provider_instance: HybridDiscoveryProvider | None = None


def get_hybrid_discovery_provider() -> HybridDiscoveryProvider:
    """Return the singleton hybrid discovery provider."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = HybridDiscoveryProvider()
    return _provider_instance
