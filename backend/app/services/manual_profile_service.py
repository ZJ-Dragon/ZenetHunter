"""Manual profile service for matching and migration."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.device import DeviceModel
from app.models.db.manual_override import ManualOverrideModel
from app.repositories.device_manual_profile import DeviceManualProfileRepository
from app.services.fingerprint_key import generate_fingerprint_key

logger = logging.getLogger(__name__)


def build_match_keys(
    *,
    mac: str | None,
    fingerprint_components: dict[str, Any] | None = None,
    ip_hint: str | None = None,
) -> dict[str, Any]:
    """Normalize a small set of match keys for profile matching."""
    keys: dict[str, Any] = {}
    if mac:
        keys["mac"] = mac.lower()
        mac_clean = mac.replace(":", "").replace("-", "").lower()
        if len(mac_clean) >= 6:
            keys["oui"] = mac_clean[:6]
    if fingerprint_components:
        for k in ("dhcp_hostname", "mdns_services", "ssdp_server", "user_agent_type"):
            if v := fingerprint_components.get(k):
                keys[k] = v
    if ip_hint:
        keys["ip_hint"] = ip_hint
    return keys


@dataclass
class ManualMatchResult:
    profile_id: int
    manual_name: str | None
    manual_vendor: str | None


class ManualProfileService:
    """High-level helpers for manual profile persistence and matching."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DeviceManualProfileRepository(session)

    async def create_or_update_profile(
        self,
        *,
        mac: str | None,
        manual_name: str | None,
        manual_vendor: str | None,
        fingerprint_key: str | None,
        match_keys: dict[str, Any],
        ip_hint: str | None = None,
        keywords: list[str] | None = None,
    ) -> ManualMatchResult:
        profile = await self.repo.upsert(
            fingerprint_key=fingerprint_key,
            manual_name=manual_name,
            manual_vendor=manual_vendor,
            match_keys=match_keys,
            mac=mac,
            ip_hint=ip_hint,
            keywords=keywords,
        )
        return ManualMatchResult(
            profile_id=profile.id,
            manual_name=profile.manual_name,
            manual_vendor=profile.manual_vendor,
        )

    async def match_manual_profile(
        self,
        *,
        mac: str | None,
        fingerprint_key: str | None,
        match_keys: dict[str, Any],
        ip_hint: str | None = None,
    ) -> ManualMatchResult | None:
        profile = await self.repo.find_best_match(
            fingerprint_key=fingerprint_key,
            mac=mac,
            match_keys=match_keys,
            ip_hint=ip_hint,
        )
        if not profile:
            return None
        return ManualMatchResult(
            profile_id=profile.id,
            manual_name=profile.manual_name,
            manual_vendor=profile.manual_vendor,
        )


async def migrate_manual_labels(session: AsyncSession) -> None:
    """One-time migration: move device/manual_override labels into manual profiles."""
    repo = DeviceManualProfileRepository(session)

    # Migrate legacy device manual fields
    devices_with_manuals = await session.execute(
        select(DeviceModel).where(
            (DeviceModel.name_manual.is_not(None))
            | (DeviceModel.vendor_manual.is_not(None))
        )
    )
    migrated = 0
    for dev in devices_with_manuals.scalars().all():
        evidence = {}
        if dev.recognition_evidence:
            try:
                evidence = json.loads(dev.recognition_evidence) or {}
            except Exception:
                evidence = {}
        fingerprint_key, components = generate_fingerprint_key(
            fingerprint_data=evidence,
            mac=dev.mac,
            vendor_guess=dev.vendor_guess,
            model_guess=dev.model_guess,
        )
        match_keys = build_match_keys(
            mac=dev.mac,
            fingerprint_components=components,
            vendor_guess=dev.vendor_guess,
            model_guess=dev.model_guess,
        )
        profile = await repo.upsert(
            fingerprint_key=fingerprint_key,
            manual_name=dev.name_manual,
            manual_vendor=dev.vendor_manual,
            match_keys=match_keys,
            mac=dev.mac,
            keywords=[],
        )
        dev.manual_profile_id = profile.id
        dev.name_manual = None
        dev.vendor_manual = None
        dev.manual_override_at = None
        dev.manual_override_by = None
        migrated += 1

    # Migrate manual_overrides table entries if present
    try:
        overrides = await session.execute(select(ManualOverrideModel))
        for override in overrides.scalars().all():
            components = {}
            if override.fingerprint_components:
                try:
                    components = json.loads(override.fingerprint_components) or {}
                except Exception:
                    components = {}
            match_keys = build_match_keys(
                mac=override.source_mac,
                fingerprint_components=components,
            )
            await repo.upsert(
                fingerprint_key=override.fingerprint_key,
                manual_name=override.manual_name,
                manual_vendor=override.manual_vendor,
                match_keys=match_keys,
                mac=override.source_mac,
                ip_hint=override.source_ip,
                keywords=[],
            )
            migrated += 1
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Manual override migration skipped: %s", exc)

    if migrated:
        logger.info("Migrated %s manual labels into device_manual_profiles", migrated)
