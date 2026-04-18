"""Application-layer scan orchestration workflow."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.database import get_session_factory
from app.domain.devices import guess_device_type
from app.domain.interfaces.providers import (
    DiscoveredDevice,
    DiscoveryRequest,
    ProbeObservation,
)
from app.models.device import Device, DeviceStatus, DeviceType
from app.providers.discovery import get_hybrid_discovery_provider
from app.providers.fingerprint import get_observation_fingerprint_extractor
from app.providers.probe import get_composite_probe_provider
from app.repositories.device import DeviceRepository
from app.repositories.device_fingerprint import DeviceFingerprintRepository
from app.repositories.event_log import EventLogRepository
from app.repositories.probe_observation import ProbeObservationRepository
from app.services.device_model_lookup import get_device_model_lookup
from app.services.keyword_extractor import KeywordExtractor
from app.services.manual_override_service import ManualOverrideService
from app.services.recognition_engine import get_recognition_engine
from app.services.state import get_state_manager
from app.services.websocket import get_connection_manager

ProgressCallback = Callable[[str, dict[str, Any]], Awaitable[None]]


@dataclass(slots=True)
class ScanWorkflowResult:
    """Result produced by the explicit backend scan workflow."""

    scan_id: str
    devices: list[Device] = field(default_factory=list)
    new_devices: list[Device] = field(default_factory=list)
    updated_devices: list[Device] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)


class ScanWorkflowService:
    """Explicit scan orchestration for discovery, recognition, and UI refresh."""

    def __init__(self):
        self.discovery_provider = get_hybrid_discovery_provider()
        self.probe_provider = get_composite_probe_provider()
        self.fingerprint_extractor = get_observation_fingerprint_extractor()
        self.model_lookup = get_device_model_lookup()
        self.recognition_engine = get_recognition_engine()
        self.keyword_extractor = KeywordExtractor()
        self.session_factory = get_session_factory()

    async def execute(
        self,
        *,
        scan_id: str,
        target_subnets: list[str],
        gateway_ip: str | None,
        detection_method: str,
        progress_callback: ProgressCallback | None = None,
    ) -> ScanWorkflowResult:
        state_manager = get_state_manager()
        ws_manager = get_connection_manager()
        stats = {
            "scan_id": scan_id,
            "target_subnets": target_subnets,
            "detection_method": detection_method,
            "started_at": datetime.now(UTC).isoformat(),
            "discovered_count": 0,
            "observation_count": 0,
            "recognized_count": 0,
            "manual_match_count": 0,
            "devices_found": 0,
        }

        if progress_callback:
            await progress_callback(
                "scanProgress",
                {
                    "stage": "discovery",
                    "message": "Discovering devices...",
                    "target_subnets": target_subnets,
                },
            )

        discovered = await self.discovery_provider.discover(
            DiscoveryRequest(target_subnets=target_subnets, scan_run_id=scan_id)
        )
        stats["discovered_count"] = len(discovered)

        if progress_callback:
            await progress_callback(
                "scanProgress",
                {
                    "stage": "observations",
                    "message": (
                        "Collecting observations for " f"{len(discovered)} devices..."
                    ),
                    "discovered_count": len(discovered),
                },
            )

        result = ScanWorkflowResult(scan_id=scan_id, stats=stats)
        if not discovered:
            stats["completed_at"] = datetime.now(UTC).isoformat()
            return result

        pending_refresh: list[tuple[Device, bool]] = []

        async with self.session_factory() as session:
            repo = DeviceRepository(session)
            fp_repo = DeviceFingerprintRepository(session)
            obs_repo = ProbeObservationRepository(session)
            event_repo = EventLogRepository(session)
            manual_override_service = ManualOverrideService(session)

            for discovered_device in discovered:
                if not discovered_device.mac:
                    continue

                observations = await self.probe_provider.probe(discovered_device)
                stats["observation_count"] += len(observations)

                fingerprint = self.fingerprint_extractor.extract(
                    discovered_device, observations
                )
                recognition = await self._recognize_device(
                    discovered_device, fingerprint
                )
                if recognition.get("confidence", 0) > 0:
                    stats["recognized_count"] += 1

                existing_device = await repo.get_by_mac(discovered_device.mac)
                baseline_device = self._build_device(
                    existing_device=existing_device,
                    discovered_device=discovered_device,
                    recognition=recognition,
                    gateway_ip=gateway_ip,
                )

                for observation in observations:
                    await self._persist_observation(
                        obs_repo=obs_repo,
                        event_repo=event_repo,
                        scan_id=scan_id,
                        device_mac=discovered_device.mac,
                        observation=observation,
                    )

                await fp_repo.upsert(
                    discovered_device.mac,
                    {
                        **fingerprint,
                        **recognition,
                    },
                )

                baseline_device = await repo.upsert(baseline_device)

                manual_override = (
                    await manual_override_service.check_and_apply_override(
                        mac=discovered_device.mac,
                        fingerprint_data=fingerprint,
                        vendor_guess=baseline_device.vendor_guess,
                        model_guess=baseline_device.model_guess,
                    )
                )
                if manual_override:
                    stats["manual_match_count"] += 1
                    baseline_device.manual_profile_id = manual_override.get(
                        "manual_profile_id"
                    )
                    if manual_override.get("name_manual"):
                        baseline_device.name_manual = manual_override["name_manual"]
                    if manual_override.get("vendor_manual"):
                        baseline_device.vendor_manual = manual_override["vendor_manual"]
                    baseline_device.manual_override_at = datetime.now(UTC)
                    baseline_device.manual_override_by = manual_override.get(
                        "match_source", "auto-match"
                    )
                    baseline_device = await repo.upsert(baseline_device)

                is_new = existing_device is None
                pending_refresh.append((baseline_device, is_new))
                result.devices.append(baseline_device)
                if is_new:
                    result.new_devices.append(baseline_device)
                else:
                    result.updated_devices.append(baseline_device)

            await session.commit()

        for device, is_new in pending_refresh:
            state_manager.update_device(device, emit_events=False)
            if is_new:
                await ws_manager.broadcast(
                    {
                        "event": "deviceAdded",
                        "data": device.model_dump(mode="json"),
                    }
                )
            else:
                await ws_manager.broadcast(
                    {
                        "event": "deviceRecognitionUpdated",
                        "data": {
                            "mac": device.mac,
                            "vendor_guess": device.vendor_guess,
                            "model_guess": device.model_guess,
                            "confidence": device.recognition_confidence,
                            "evidence": device.recognition_evidence,
                            "display_name": device.display_name,
                            "display_vendor": device.display_vendor,
                            "timestamp": datetime.now(UTC).isoformat(),
                        },
                    }
                )
            await ws_manager.broadcast(
                {
                    "event": "scanLog",
                    "data": {
                        "level": "info",
                        "message": f"Discovered device: {device.ip} ({device.mac})",
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )

        stats["devices_found"] = len(result.devices)
        stats["completed_at"] = datetime.now(UTC).isoformat()
        return result

    async def _recognize_device(
        self, discovered_device: DiscoveredDevice, fingerprint: dict[str, Any]
    ) -> dict[str, Any]:
        existing_vendor, _existing_model = self.model_lookup.lookup_vendor_and_model(
            discovered_device.mac or ""
        )
        return await self.recognition_engine.recognize_device(
            mac=discovered_device.mac or "",
            fingerprint=fingerprint,
            existing_vendor=existing_vendor,
        )

    def _build_device(
        self,
        *,
        existing_device: Device | None,
        discovered_device: DiscoveredDevice,
        recognition: dict[str, Any],
        gateway_ip: str | None,
    ) -> Device:
        lookup_vendor, lookup_model = self.model_lookup.lookup_vendor_and_model(
            discovered_device.mac or ""
        )
        vendor_guess = recognition.get("best_guess_vendor") or lookup_vendor
        model_guess = recognition.get("best_guess_model") or lookup_model
        vendor = (
            (existing_device and existing_device.vendor)
            or lookup_vendor
            or recognition.get("best_guess_vendor")
        )
        model = (
            (existing_device and existing_device.model)
            or lookup_model
            or recognition.get("best_guess_model")
        )
        name = (
            existing_device and existing_device.name
        ) or discovered_device.metadata.get("hostname")
        device_type = guess_device_type(
            ip=discovered_device.ip,
            vendor=vendor or vendor_guess,
            model=model or model_guess,
            gateway_ip=gateway_ip,
        )
        now = datetime.now(UTC)

        if existing_device:
            existing_device.ip = discovered_device.ip
            existing_device.name = name
            existing_device.vendor = vendor
            existing_device.model = model
            existing_device.type = (
                existing_device.type
                if existing_device.type != DeviceType.UNKNOWN
                else device_type
            )
            existing_device.status = DeviceStatus.ONLINE
            existing_device.last_seen = now
            existing_device.vendor_guess = vendor_guess
            existing_device.model_guess = model_guess
            existing_device.recognition_confidence = recognition.get("confidence")
            existing_device.recognition_evidence = recognition.get("evidence")
            existing_device.discovery_source = discovered_device.source
            existing_device.freshness_score = discovered_device.metadata.get(
                "freshness_score"
            )
            return existing_device

        return Device(
            mac=discovered_device.mac or "00:00:00:00:00:00",
            ip=discovered_device.ip,
            name=name,
            vendor=vendor,
            model=model,
            type=device_type,
            status=DeviceStatus.ONLINE,
            first_seen=now,
            last_seen=now,
            vendor_guess=vendor_guess,
            model_guess=model_guess,
            recognition_confidence=recognition.get("confidence"),
            recognition_evidence=recognition.get("evidence"),
            discovery_source=discovered_device.source,
            freshness_score=discovered_device.metadata.get("freshness_score"),
        )

    async def _persist_observation(
        self,
        *,
        obs_repo: ProbeObservationRepository,
        event_repo: EventLogRepository,
        scan_id: str,
        device_mac: str,
        observation: ProbeObservation,
    ) -> None:
        keywords = self.keyword_extractor.extract(observation.key_fields)
        keyword_hits = self.keyword_extractor.match_rules(
            keywords, observation.key_fields
        )
        record = await obs_repo.add(
            device_mac=device_mac,
            scan_run_id=scan_id,
            protocol=observation.protocol,
            key_fields=observation.key_fields,
            keywords=keywords,
            keyword_hits=keyword_hits,
            raw_summary=observation.summary,
            redaction_level="standard",
        )
        await event_repo.add_log(
            level="INFO",
            module="observation",
            message="Probe observation captured",
            device_mac=device_mac,
            context={
                "observation_id": record.id,
                "protocol": observation.protocol,
            },
        )


_workflow_instance: ScanWorkflowService | None = None


def get_scan_workflow_service() -> ScanWorkflowService:
    """Return the singleton scan workflow service."""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = ScanWorkflowService()
    return _workflow_instance
