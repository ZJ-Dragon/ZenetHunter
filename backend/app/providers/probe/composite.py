"""Composite probe provider for enrichment observations."""

from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.domain.interfaces.providers import (
    DiscoveredDevice,
    ProbeObservation,
    ProbeProvider,
)
from app.services.observation_recorder import build_key_fields, build_summary


class CompositeProbeProvider(ProbeProvider):
    """Run the configured lightweight enrichment probes for a device."""

    name = "composite-probe"

    def __init__(self):
        self.settings = get_settings()

    async def probe(self, device: DiscoveredDevice) -> list[ProbeObservation]:
        observations: list[ProbeObservation] = []

        if self.settings.feature_mdns:
            from app.services.scanner.enrich.mdns import enrich_with_mdns

            data = await _safe_probe(
                enrich_with_mdns(
                    device_ip=device.ip,
                    device_mac=device.mac or "",
                    timeout=2.0,
                )
            )
            _append_observation(observations, "mdns", data)

        if self.settings.feature_ssdp:
            from app.services.scanner.enrich.ssdp import enrich_with_ssdp

            data = await _safe_probe(
                enrich_with_ssdp(
                    device_ip=device.ip,
                    device_mac=device.mac or "",
                    timeout=2.0,
                )
            )
            _append_observation(observations, "ssdp", data)

        if self.settings.feature_active_probe:
            from app.services.scanner.enrich.active_probe import (
                enrich_with_active_probe,
            )

            data = await _safe_probe(
                enrich_with_active_probe(
                    device_ip=device.ip,
                    device_mac=device.mac or "",
                    timeout=2.0,
                )
            )
            _append_observation(observations, "active_probe", data)

        return observations


async def _safe_probe(coro) -> dict | None:
    try:
        return await asyncio.wait_for(coro, timeout=3.0)
    except Exception:
        return None


def _append_observation(
    observations: list[ProbeObservation], protocol: str, raw_fields: dict | None
) -> None:
    if not raw_fields:
        return

    key_fields = build_key_fields(protocol, raw_fields)
    if not key_fields:
        return

    observations.append(
        ProbeObservation(
            protocol=protocol,
            key_fields=key_fields,
            raw_fields=raw_fields,
            summary=build_summary(protocol, key_fields),
            evidence_sources=[protocol],
        )
    )


_provider_instance: CompositeProbeProvider | None = None


def get_composite_probe_provider() -> CompositeProbeProvider:
    """Return the singleton composite probe provider."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = CompositeProbeProvider()
    return _provider_instance
