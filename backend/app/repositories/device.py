"""Device repository for database operations."""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attack import AttackStatus
from app.models.db.device import DeviceModel, DeviceStatusEnum, DeviceTypeEnum
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
            type=DeviceTypeEnum(device.type.value),
            status=DeviceStatusEnum(device.status.value),
            attack_status=device.attack_status.value,
            defense_status=device.defense_status.value,
            active_defense_policy=(
                device.active_defense_policy.value
                if device.active_defense_policy
                else None
            ),
            first_seen=device.first_seen,
            last_seen=device.last_seen,
            tags=json.dumps(device.tags) if device.tags else None,
            alias=device.alias,
        )
        self.session.add(device_model)
        await self.session.flush()
        return device_model

    async def get_by_mac(self, mac: str) -> Device | None:
        """Get a device by MAC address."""
        result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.mac == mac.lower())
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self.to_domain_model(model)

    async def upsert(self, device: Device) -> Device:
        """Insert or update a device based on MAC address.

        Args:
            device: Device model to upsert

        Returns:
            Updated Device domain model
        """
        mac_lower = device.mac.lower()
        result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.mac == mac_lower)
        )
        db_device = result.scalar_one_or_none()

        if db_device:
            # Update existing device
            db_device.ip = str(device.ip)
            db_device.name = device.name
            db_device.vendor = device.vendor
            db_device.model = device.model
            db_device.type = DeviceTypeEnum(device.type.value)
            db_device.status = DeviceStatusEnum(device.status.value)
            db_device.attack_status = device.attack_status.value
            db_device.defense_status = device.defense_status.value
            db_device.active_defense_policy = (
                device.active_defense_policy.value
                if device.active_defense_policy
                else None
            )
            db_device.last_seen = device.last_seen
            db_device.tags = json.dumps(device.tags) if device.tags else None
            db_device.alias = device.alias
            db_device.vendor_guess = device.vendor_guess
            db_device.model_guess = device.model_guess
            db_device.recognition_confidence = device.recognition_confidence
            db_device.recognition_evidence = (
                json.dumps(device.recognition_evidence)
                if device.recognition_evidence
                else None
            )
            # Update first_seen only if it's earlier than current
            # Ensure both datetimes are timezone-aware before comparison
            device_first_seen = (
                device.first_seen.replace(tzinfo=UTC)
                if device.first_seen.tzinfo is None
                else device.first_seen
            )
            db_first_seen = (
                db_device.first_seen.replace(tzinfo=UTC)
                if db_device.first_seen.tzinfo is None
                else db_device.first_seen
            )
            if device_first_seen < db_first_seen:
                db_device.first_seen = device_first_seen
        else:
            # Create new device
            db_device = DeviceModel(
                mac=mac_lower,
                ip=str(device.ip),
                name=device.name,
                vendor=device.vendor,
                model=device.model,
                type=DeviceTypeEnum(device.type.value),
                status=DeviceStatusEnum(device.status.value),
                attack_status=device.attack_status.value,
                defense_status=device.defense_status.value,
                active_defense_policy=(
                    device.active_defense_policy.value
                    if device.active_defense_policy
                    else None
                ),
                first_seen=device.first_seen,
                last_seen=device.last_seen,
                tags=json.dumps(device.tags) if device.tags else None,
                alias=device.alias,
                vendor_guess=device.vendor_guess,
                model_guess=device.model_guess,
                recognition_confidence=device.recognition_confidence,
                recognition_evidence=(
                    json.dumps(device.recognition_evidence)
                    if device.recognition_evidence
                    else None
                ),
            )
            self.session.add(db_device)

        await self.session.flush()
        return self.to_domain_model(db_device)

    async def get_all(self) -> list[Device]:
        """Get all devices."""
        result = await self.session.execute(select(DeviceModel))
        models = result.scalars().all()
        return [self.to_domain_model(model) for model in models]

    async def update(self, device: Device) -> Device | None:
        """Update an existing device."""
        db_device = await self.session.execute(
            select(DeviceModel).where(DeviceModel.mac == device.mac.lower())
        )
        device_model = db_device.scalar_one_or_none()
        if not device_model:
            return None

        device_model.ip = str(device.ip)
        device_model.name = device.name
        device_model.vendor = device.vendor
        device_model.model = device.model
        device_model.type = DeviceTypeEnum(device.type.value)
        device_model.status = DeviceStatusEnum(device.status.value)
        device_model.attack_status = device.attack_status.value
        device_model.defense_status = device.defense_status.value
        device_model.active_defense_policy = (
            device.active_defense_policy.value if device.active_defense_policy else None
        )
        device_model.last_seen = device.last_seen
        device_model.tags = json.dumps(device.tags) if device.tags else None
        device_model.alias = device.alias

        await self.session.flush()
        return self.to_domain_model(device_model)

    async def delete(self, mac: str) -> bool:
        """Delete a device by MAC address."""
        result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.mac == mac.lower())
        )
        device_model = result.scalar_one_or_none()
        if not device_model:
            return False

        await self.session.delete(device_model)
        await self.session.flush()
        return True

    async def clear_all(self) -> int:
        """Clear all devices from the database."""
        from sqlalchemy import delete

        # Count devices before deletion
        result = await self.session.execute(select(DeviceModel))
        count = len(result.scalars().all())

        # Use bulk delete for efficiency
        await self.session.execute(delete(DeviceModel))
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
            type=DeviceType(device_model.type.value),
            status=DeviceStatus(device_model.status.value),
            attack_status=AttackStatus(device_model.attack_status),
            defense_status=DefenseStatus(device_model.defense_status),
            active_defense_policy=(
                DefenseType(device_model.active_defense_policy)
                if device_model.active_defense_policy
                else None
            ),
            first_seen=device_model.first_seen,
            last_seen=device_model.last_seen,
            tags=json.loads(device_model.tags) if device_model.tags else [],
            alias=device_model.alias,
            vendor_guess=getattr(device_model, "vendor_guess", None),
            model_guess=getattr(device_model, "model_guess", None),
            recognition_confidence=getattr(
                device_model, "recognition_confidence", None
            ),
            recognition_evidence=(
                json.loads(device_model.recognition_evidence)
                if getattr(device_model, "recognition_evidence", None)
                else None
            ),
        )


# Dependency injection for FastAPI
def get_device_repository(session: AsyncSession) -> DeviceRepository:
    """Get device repository instance."""
    return DeviceRepository(session)
