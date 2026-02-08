"""Repository for device manual profiles."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.device_manual_profile import DeviceManualProfileModel
from app.models.manual_profile import DeviceManualProfile


class DeviceManualProfileRepository:
    """Data access for manual profile records."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(
        self,
        *,
        fingerprint_key: str | None,
        manual_name: str | None,
        manual_vendor: str | None,
        match_keys: dict[str, Any] | None = None,
        mac: str | None = None,
        ip_hint: str | None = None,
        keywords: list[str] | None = None,
    ) -> DeviceManualProfile:
        """Create or update a manual profile by fingerprint_key (if provided)."""
        profile = None
        if fingerprint_key:
            profile = await self.get_by_fingerprint_key(fingerprint_key)

        if profile:
            profile.manual_name = manual_name
            profile.manual_vendor = manual_vendor
            profile.match_keys = match_keys or {}
            profile.mac = mac
            profile.ip_hint = ip_hint
            profile.keywords = keywords or []
            profile.updated_at = datetime.now(UTC)
        else:
            profile = DeviceManualProfileModel(
                manual_name=manual_name,
                manual_vendor=manual_vendor,
                fingerprint_key=fingerprint_key,
                match_keys=match_keys or {},
                mac=mac.lower() if mac else None,
                ip_hint=ip_hint,
                keywords=keywords or [],
            )
            self.session.add(profile)

        await self.session.flush()
        return DeviceManualProfile.model_validate(profile)

    async def get_by_fingerprint_key(
        self, fingerprint_key: str
    ) -> DeviceManualProfileModel | None:
        result = await self.session.execute(
            select(DeviceManualProfileModel).where(
                DeviceManualProfileModel.fingerprint_key == fingerprint_key
            )
        )
        return result.scalar_one_or_none()

    async def get_by_mac(self, mac: str) -> DeviceManualProfileModel | None:
        result = await self.session.execute(
            select(DeviceManualProfileModel).where(
                DeviceManualProfileModel.mac == mac.lower()
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[DeviceManualProfile]:
        result = await self.session.execute(select(DeviceManualProfileModel))
        return [DeviceManualProfile.model_validate(p) for p in result.scalars().all()]

    async def find_best_match(
        self,
        *,
        fingerprint_key: str | None,
        mac: str | None,
        match_keys: dict[str, Any] | None = None,
    ) -> DeviceManualProfile | None:
        """Find the best matching manual profile using heuristics."""
        match_keys = match_keys or {}
        mac_lower = mac.lower() if mac else None

        # Fetch candidates lazily; table expected to be small
        result = await self.session.execute(select(DeviceManualProfileModel))
        candidates = list(result.scalars().all())

        best = None
        best_score = 0

        for profile in candidates:
            score = 0
            if fingerprint_key and profile.fingerprint_key == fingerprint_key:
                score += 100
            if mac_lower and profile.mac and profile.mac == mac_lower:
                score += 80

            if match_keys and profile.match_keys:
                score += self._score_match_keys(profile.match_keys, match_keys)

            if score > best_score:
                best = profile
                best_score = score

        if best:
            return DeviceManualProfile.model_validate(best)
        return None

    @staticmethod
    def _score_match_keys(
        profile_keys: dict[str, Any], incoming: dict[str, Any]
    ) -> int:
        """Lightweight scoring for match_keys intersection."""
        score = 0

        def normalize(val: Any) -> set[str]:
            if val is None:
                return set()
            if isinstance(val, (list, tuple, set)):
                return {str(v).lower() for v in val if v is not None}
            try:
                if isinstance(val, str):
                    return {val.lower()}
                return {str(val).lower()}
            except Exception:
                return set()

        for key, p_val in profile_keys.items():
            incoming_val = incoming.get(key)
            if incoming_val is None:
                continue
            p_norm = normalize(p_val)
            i_norm = normalize(incoming_val)
            if not p_norm or not i_norm:
                continue
            # Reward overlap, capped
            overlap = len(p_norm.intersection(i_norm))
            if overlap:
                score += min(10, overlap * 5)

        return score
