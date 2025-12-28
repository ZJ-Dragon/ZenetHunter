"""Device repository for database operations."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attack import AttackStatus
from app.models.db.device import DeviceModel
from app.models.defender import DefenseStatus, DefenseType
from app.models.device import Device, DeviceStatus, DeviceType


class DeviceRepository:
    """Repository for device database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, device: Device) -> DeviceModel:
        """Create a new device in the database."""
        device_model = DeviceModel(
            mac=device.mac.lower(),
            ip=str(device.ip),
            name=device.name,
            vendor=device.vendor,
            model=device.model,
            type=device.type.value,
            status=device.status.value,
            attack_status=device.attack_status.value,
            defense_status=device.defense_status.value,
            active_defense_policy=(
                device.active_defense_policy.value
                if device.active_defense_policy
                else None
            ),
            first_seen=device.first_seen,
            last_seen=device.last_seen,
            tags=device.tags or [],
            alias=device.alias,
        )
        self.session.add(device_model)
        await self.session.flush()
        return device_model

    async def get_by_mac(self, mac: str) -> DeviceModel | None:
        """Get a device by MAC address."""
        result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.mac == mac.lower())
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[DeviceModel]:
        """Get all devices."""
        result = await self.session.execute(select(DeviceModel))
        return list(result.scalars().all())

    async def update(self, device: Device) -> DeviceModel | None:
        """Update an existing device."""
        device_model = await self.get_by_mac(device.mac)
        if not device_model:
            return None

        device_model.ip = str(device.ip)
        device_model.name = device.name
        device_model.vendor = device.vendor
        device_model.model = device.model
        device_model.type = device.type.value
        device_model.status = device.status.value
        device_model.attack_status = device.attack_status.value
        device_model.defense_status = device.defense_status.value
        device_model.active_defense_policy = (
            device.active_defense_policy.value if device.active_defense_policy else None
        )
        device_model.last_seen = device.last_seen
        device_model.tags = device.tags or []
        device_model.alias = device.alias

        await self.session.flush()
        return device_model

    async def delete(self, mac: str) -> bool:
        """Delete a device by MAC address."""
        device_model = await self.get_by_mac(mac)
        if not device_model:
            return False

        await self.session.delete(device_model)
        await self.session.flush()
        return True

    async def clear_all(self) -> int:
        """Clear all devices from the database."""
        result = await self.session.execute(select(DeviceModel))
        devices = result.scalars().all()
        count = len(devices)
        for device in devices:
            await self.session.delete(device)
        await self.session.flush()
        return count

    async def update_last_seen(
        self, mac: str, timestamp: datetime | None = None
    ) -> None:
        """Update the last_seen timestamp for a device."""
        if timestamp is None:
            timestamp = datetime.now(UTC)
        await self.session.execute(
            update(DeviceModel)
            .where(DeviceModel.mac == mac.lower())
            .values(last_seen=timestamp)
        )
        await self.session.flush()

    async def update_attack_status(
        self, mac: str, status: AttackStatus
    ) -> DeviceModel | None:
        """Update attack status for a device."""
        result = await self.session.execute(
            update(DeviceModel)
            .where(DeviceModel.mac == mac.lower())
            .values(attack_status=status.value)
            .returning(DeviceModel)
        )
        await self.session.flush()
        return result.scalar_one_or_none()

    async def update_defense_status(
        self, mac: str, status: DefenseStatus, policy: DefenseType | None = None
    ) -> DeviceModel | None:
        """Update defense status and policy for a device."""
        update_values: dict[str, Any] = {"defense_status": status.value}
        if policy is not None:
            update_values["active_defense_policy"] = policy.value
        elif status == DefenseStatus.INACTIVE:
            update_values["active_defense_policy"] = None

        result = await self.session.execute(
            update(DeviceModel)
            .where(DeviceModel.mac == mac.lower())
            .values(**update_values)
            .returning(DeviceModel)
        )
        await self.session.flush()
        return result.scalar_one_or_none()

    def to_domain_model(self, device_model: DeviceModel) -> Device:
        """Convert database model to domain model."""
        return Device(
            mac=device_model.mac,
            ip=device_model.ip,
            name=device_model.name,
            vendor=device_model.vendor,
            model=device_model.model,
            type=DeviceType(device_model.type),
            status=DeviceStatus(device_model.status),
            attack_status=AttackStatus(device_model.attack_status),
            defense_status=DefenseStatus(device_model.defense_status),
            active_defense_policy=(
                DefenseType(device_model.active_defense_policy)
                if device_model.active_defense_policy
                else None
            ),
            first_seen=device_model.first_seen,
            last_seen=device_model.last_seen,
            tags=device_model.tags or [],
            alias=device_model.alias,
        )


# Dependency injection for FastAPI
def get_device_repository(session: AsyncSession) -> DeviceRepository:
    """Get device repository instance."""
    return DeviceRepository(session)
