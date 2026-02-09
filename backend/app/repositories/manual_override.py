"""Manual Override repository for database operations."""

import json
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.manual_override import ManualOverrideModel


class ManualOverrideRepository:
    """Repository for manual override database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_fingerprint_key(
        self, fingerprint_key: str
    ) -> ManualOverrideModel | None:
        """Get a manual override by fingerprint key."""
        result = await self.session.execute(
            select(ManualOverrideModel).where(
                ManualOverrideModel.fingerprint_key == fingerprint_key
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        fingerprint_key: str,
        manual_name: str | None = None,
        manual_vendor: str | None = None,
        source_mac: str | None = None,
        source_ip: str | None = None,
        fingerprint_components: dict | None = None,
        username: str | None = None,
    ) -> ManualOverrideModel:
        """Insert or update a manual override.

        Args:
            fingerprint_key: Normalized fingerprint key
            manual_name: User-provided device name
            manual_vendor: User-provided vendor name
            source_mac: MAC address of source device
            source_ip: IP address of source device
            fingerprint_components: Dict of components used to generate key
            username: Username who made the change

        Returns:
            Created or updated ManualOverrideModel
        """
        result = await self.session.execute(
            select(ManualOverrideModel).where(
                ManualOverrideModel.fingerprint_key == fingerprint_key
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing override
            existing.manual_name = manual_name
            existing.manual_vendor = manual_vendor
            existing.updated_at = datetime.now(UTC)
            existing.updated_by = username
            if source_mac:
                existing.source_mac = source_mac
            if source_ip:
                existing.source_ip = source_ip
            if fingerprint_components:
                existing.fingerprint_components = json.dumps(fingerprint_components)
            await self.session.flush()
            return existing
        else:
            # Create new override
            override = ManualOverrideModel(
                fingerprint_key=fingerprint_key,
                manual_name=manual_name,
                manual_vendor=manual_vendor,
                source_mac=source_mac,
                source_ip=source_ip,
                fingerprint_components=(
                    json.dumps(fingerprint_components)
                    if fingerprint_components
                    else None
                ),
                created_by=username,
                updated_by=username,
            )
            self.session.add(override)
            await self.session.flush()
            return override

    async def increment_match_count(self, fingerprint_key: str) -> None:
        """Increment the match count for an override."""
        await self.session.execute(
            update(ManualOverrideModel)
            .where(ManualOverrideModel.fingerprint_key == fingerprint_key)
            .values(match_count=ManualOverrideModel.match_count + 1)
        )
        await self.session.flush()

    async def get_all(self) -> list[ManualOverrideModel]:
        """Get all manual overrides."""
        result = await self.session.execute(select(ManualOverrideModel))
        return list(result.scalars().all())

    async def delete_by_fingerprint_key(self, fingerprint_key: str) -> bool:
        """Delete a manual override by fingerprint key."""
        result = await self.session.execute(
            select(ManualOverrideModel).where(
                ManualOverrideModel.fingerprint_key == fingerprint_key
            )
        )
        override = result.scalar_one_or_none()
        if not override:
            return False

        await self.session.delete(override)
        await self.session.flush()
        return True


def get_manual_override_repository(session: AsyncSession) -> ManualOverrideRepository:
    """Get manual override repository instance."""
    return ManualOverrideRepository(session)
