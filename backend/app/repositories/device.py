"""Device repository for database operations."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.device import DeviceModel, DeviceStatusEnum, DeviceTypeEnum
from app.models.device import Device, DeviceStatus, DeviceType

logger = logging.getLogger(__name__)


class DeviceRepository:
    """Repository for device database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Device]:
        """Get all devices.

        Returns:
            List of Device models
        """
        result = await self.session.execute(select(DeviceModel))
        models = result.scalars().all()
        return [self._model_to_domain(model) for model in models]

    async def get_by_mac(self, mac: str) -> Device | None:
        """Get device by MAC address.

        Args:
            mac: MAC address (normalized to lowercase)

        Returns:
            Device model or None if not found
        """
        mac_lower = mac.lower()
        result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.mac == mac_lower)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_domain(model)

    async def upsert(self, device: Device) -> Device:
        """Insert or update device.

        Args:
            device: Device model to upsert

        Returns:
            Updated Device model
        """
        mac_lower = device.mac.lower()
        result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.mac == mac_lower)
        )
        model = result.scalar_one_or_none()

        if model is None:
            # Create new device
            model = DeviceModel(
                mac=mac_lower,
                ip=str(device.ip),
                name=device.name,
                vendor=device.vendor,
                model=device.model,
                type=self._domain_type_to_db(device.type),
                status=self._domain_status_to_db(device.status),
                attack_status=device.attack_status,
                defense_status=device.defense_status,
                active_defense_policy=device.active_defense_policy,
                first_seen=device.first_seen,
                last_seen=device.last_seen,
            )
            self.session.add(model)
        else:
            # Update existing device
            model.ip = str(device.ip)
            model.name = device.name
            model.vendor = device.vendor
            model.model = device.model
            model.type = self._domain_type_to_db(device.type)
            model.status = self._domain_status_to_db(device.status)
            model.attack_status = device.attack_status
            model.defense_status = device.defense_status
            model.active_defense_policy = device.active_defense_policy
            model.last_seen = datetime.now(UTC)

        await self.session.flush()
        return self._model_to_domain(model)

    async def update_status(self, mac: str, status: DeviceStatus) -> Device | None:
        """Update device status.

        Args:
            mac: MAC address
            status: New status

        Returns:
            Updated Device model or None if not found
        """
        mac_lower = mac.lower()
        await self.session.execute(
            update(DeviceModel)
            .where(DeviceModel.mac == mac_lower)
            .values(
                status=self._domain_status_to_db(status), last_seen=datetime.now(UTC)
            )
        )
        await self.session.flush()
        return await self.get_by_mac(mac_lower)

    async def update_attack_status(self, mac: str, attack_status: Any) -> Device | None:
        """Update device attack status.

        Args:
            mac: MAC address
            attack_status: New attack status

        Returns:
            Updated Device model or None if not found
        """
        mac_lower = mac.lower()
        await self.session.execute(
            update(DeviceModel)
            .where(DeviceModel.mac == mac_lower)
            .values(attack_status=attack_status, last_seen=datetime.now(UTC))
        )
        await self.session.flush()
        return await self.get_by_mac(mac_lower)

    async def update_defense_status(
        self, mac: str, defense_status: Any, policy: Any | None = None
    ) -> Device | None:
        """Update device defense status.

        Args:
            mac: MAC address
            defense_status: New defense status (enum or string)
            policy: Active defense policy (optional)

        Returns:
            Updated Device model or None if not found
        """
        mac_lower = mac.lower()
        # Handle enum or string
        defense_status_value = (
            defense_status.value if hasattr(defense_status, "value") else defense_status
        )
        values = {
            "defense_status": defense_status,
            "last_seen": datetime.now(UTC),
        }
        if policy is not None:
            values["active_defense_policy"] = policy
        elif defense_status_value == "inactive":
            values["active_defense_policy"] = None

        await self.session.execute(
            update(DeviceModel).where(DeviceModel.mac == mac_lower).values(**values)
        )
        await self.session.flush()
        return await self.get_by_mac(mac_lower)

    async def clear_all(self) -> int:
        """Clear all devices from the database.

        Returns:
            Number of devices deleted
        """
        from sqlalchemy import delete
        
        result = await self.session.execute(delete(DeviceModel))
        await self.session.flush()
        deleted_count = result.rowcount if result.rowcount is not None else 0
        logger.info(f"Cleared {deleted_count} devices from database")
        return deleted_count

    def _model_to_domain(self, model: DeviceModel) -> Device:
        """Convert ORM model to domain model."""
        return Device(
            mac=model.mac,
            ip=model.ip,
            name=model.name,
            vendor=model.vendor,
            model=model.model,
            type=self._db_type_to_domain(model.type),
            status=self._db_status_to_domain(model.status),
            attack_status=model.attack_status,
            defense_status=model.defense_status,
            active_defense_policy=model.active_defense_policy,
            first_seen=model.first_seen,
            last_seen=model.last_seen,
        )

    def _domain_type_to_db(self, domain_type: DeviceType) -> DeviceTypeEnum:
        """Convert domain DeviceType to DB enum."""
        return DeviceTypeEnum(domain_type.value)

    def _db_type_to_domain(self, db_type: DeviceTypeEnum) -> DeviceType:
        """Convert DB enum to domain DeviceType."""
        return DeviceType(db_type.value)

    def _domain_status_to_db(self, domain_status: DeviceStatus) -> DeviceStatusEnum:
        """Convert domain DeviceStatus to DB enum."""
        return DeviceStatusEnum(domain_status.value)

    def _db_status_to_domain(self, db_status: DeviceStatusEnum) -> DeviceStatus:
        """Convert DB enum to domain DeviceStatus."""
        return DeviceStatus(db_status.value)


# Dependency injection for FastAPI
async def get_device_repository(session: AsyncSession) -> DeviceRepository:
    """Get device repository instance."""
    return DeviceRepository(session)
