"""Tests for the explicit scan workflow and discovery fallback behavior."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.scanning.workflow import ScanWorkflowService
from app.core.database import get_session_factory
from app.domain.interfaces.providers import (
    DiscoveredDevice,
    DiscoveryRequest,
    ProbeObservation,
)
from app.providers.discovery.hybrid import HybridDiscoveryProvider
from app.repositories.device import DeviceRepository
from app.services.scanner.candidate.dhcp_leases import DHCPCandidate
from app.services.state import get_state_manager


@pytest.mark.asyncio
async def test_hybrid_discovery_falls_back_to_unconfirmed_candidates(monkeypatch):
    """Cached candidates should not disappear when refresh cannot confirm them."""
    provider = HybridDiscoveryProvider()
    provider.capabilities = SimpleNamespace(can_arp_sweep=lambda: False)

    monkeypatch.setattr(
        "app.providers.discovery.hybrid.get_arp_candidates",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        "app.providers.discovery.hybrid.get_dhcp_candidates",
        AsyncMock(
            return_value=[
                DHCPCandidate(
                    ip="192.168.1.50",
                    mac="aa:bb:cc:dd:ee:ff",
                    hostname="lab-sensor",
                    lease_end=datetime.now(UTC),
                    source="dhcp-lease",
                )
            ]
        ),
    )
    monkeypatch.setattr(
        "app.providers.discovery.hybrid.refresh_candidates",
        AsyncMock(return_value=[]),
    )

    discovered = await provider.discover(
        DiscoveryRequest(target_subnets=["192.168.1.0/24"], scan_run_id="scan-1")
    )

    assert len(discovered) == 1
    assert discovered[0].source == "dhcp-lease"
    assert discovered[0].metadata["refresh_state"] == "unconfirmed"
    assert discovered[0].metadata["freshness_score"] == 40
    assert discovered[0].metadata["hostname"] == "lab-sensor"


class _DummyManualOverrideService:
    def __init__(self, session):
        self.session = session

    async def check_and_apply_override(self, **kwargs):
        return {
            "name_manual": "Lab Sensor",
            "vendor_manual": "Acme Corp",
            "match_source": "manual_profile",
        }


@pytest.mark.asyncio
async def test_scan_workflow_persists_display_fields_and_state(monkeypatch):
    """The explicit workflow should persist discovered devices and canonical display fields."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        await DeviceRepository(session).clear_all()
        await session.commit()

    service = ScanWorkflowService()
    service.discovery_provider = MagicMock()
    service.discovery_provider.discover = AsyncMock(
        return_value=[
            DiscoveredDevice(
                ip="192.168.1.50",
                mac="aa:bb:cc:dd:ee:ff",
                interface="en0",
                source="dhcp-lease",
                metadata={"hostname": "lab-sensor", "freshness_score": 88},
            )
        ]
    )
    service.probe_provider = MagicMock()
    service.probe_provider.probe = AsyncMock(
        return_value=[
            ProbeObservation(
                protocol="ssdp",
                key_fields={
                    "ssdp_manufacturer": "PrinterCo",
                    "ssdp_model_name": "PX-1",
                    "protocol": "ssdp",
                },
                raw_fields={
                    "ssdp_manufacturer": "PrinterCo",
                    "ssdp_model_name": "PX-1",
                },
                summary="ssdp | PX-1 | PrinterCo",
                evidence_sources=["ssdp"],
            )
        ]
    )
    service.fingerprint_extractor = MagicMock()
    service.fingerprint_extractor.extract.return_value = {
        "dhcp_opt12_hostname": "lab-sensor",
        "ssdp_manufacturer": "PrinterCo",
        "ssdp_model_name": "PX-1",
        "ip": "192.168.1.50",
        "mac": "aa:bb:cc:dd:ee:ff",
    }
    service.recognition_engine = MagicMock()
    service.recognition_engine.recognize_device = AsyncMock(
        return_value={
            "best_guess_vendor": "PrinterCo",
            "best_guess_model": "PX-1",
            "confidence": 91,
            "evidence": {"sources": ["ssdp"], "matched_fields": ["ssdp_model_name"]},
        }
    )
    service.model_lookup = MagicMock()
    service.model_lookup.lookup_vendor_and_model.return_value = (None, None)

    ws_manager = MagicMock()
    ws_manager.broadcast = AsyncMock()
    monkeypatch.setattr(
        "app.application.scanning.workflow.get_connection_manager",
        lambda: ws_manager,
    )
    monkeypatch.setattr(
        "app.application.scanning.workflow.ManualOverrideService",
        _DummyManualOverrideService,
    )

    result = await service.execute(
        scan_id="scan-2",
        target_subnets=["192.168.1.0/24"],
        gateway_ip="192.168.1.1",
        detection_method="test",
    )

    assert result.stats["devices_found"] == 1
    assert result.stats["manual_match_count"] == 1
    assert result.devices[0].display_name == "Lab Sensor"
    assert result.devices[0].display_vendor == "Acme Corp"
    assert result.devices[0].discovery_source == "dhcp-lease"
    assert result.devices[0].freshness_score == 88

    async with session_factory() as session:
        stored = await DeviceRepository(session).get_by_mac("aa:bb:cc:dd:ee:ff")

    assert stored is not None
    assert stored.display_name == "Lab Sensor"
    assert stored.display_vendor == "Acme Corp"
    assert stored.discovery_source == "dhcp-lease"
    assert stored.freshness_score == 88

    state_device = get_state_manager().get_device("aa:bb:cc:dd:ee:ff")
    assert state_device is not None
    assert state_device.display_name == "Lab Sensor"
    assert ws_manager.broadcast.await_count >= 2
