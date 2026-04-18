"""Device repository for database operations."""

import json
import logging
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attack import ActiveDefenseStatus
from app.models.db.device import DeviceModel, DeviceStatusEnum, DeviceTypeEnum
from app.models.device import Device, DeviceStatus, DeviceType
from app.models.manual_profile import DeviceManualProfile

logger = logging.getLogger(__name__)
UNSET = object()


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
            active_defense_status=device.active_defense_status.value,
            first_seen=device.first_seen,
            last_seen=device.last_seen,
            tags=json.dumps(device.tags) if device.tags else None,
            alias=device.alias,
            manual_profile_id=getattr(device, "manual_profile_id", None),
            discovery_source=getattr(device, "discovery_source", None),
            freshness_score=getattr(device, "freshness_score", None),
        )
        self.session.add(device_model)
        await self.session.flush()
        return device_model

    async def get_by_mac(self, mac: str) -> Device | None:
        """Get a device by MAC address."""
        result = await self.session.execute(
            select(DeviceModel)
            .where(DeviceModel.mac == mac.lower())
            .execution_options(populate_existing=True)
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
            db_device.active_defense_status = device.active_defense_status.value
            db_device.last_seen = device.last_seen
            db_device.tags = json.dumps(device.tags) if device.tags else None
            db_device.alias = device.alias
            db_device.vendor_guess = device.vendor_guess
            db_device.model_guess = device.model_guess
            db_device.recognition_confidence = device.recognition_confidence
            db_device.discovery_source = getattr(device, "discovery_source", None)
            db_device.freshness_score = getattr(device, "freshness_score", None)
            db_device.recognition_evidence = (
                json.dumps(device.recognition_evidence)
                if device.recognition_evidence
                else None
            )
            db_device.manual_profile_id = getattr(device, "manual_profile_id", None)
            if db_device.manual_profile_id:
                db_device.name_manual = None
                db_device.vendor_manual = None
            else:
                # Manual override fields - only update if provided (don't overwrite)
                if hasattr(device, "name_manual") and device.name_manual is not None:
                    db_device.name_manual = device.name_manual
                if (
                    hasattr(device, "vendor_manual")
                    and device.vendor_manual is not None
                ):
                    db_device.vendor_manual = device.vendor_manual
            if hasattr(device, "manual_override_at") and device.manual_override_at:
                db_device.manual_override_at = device.manual_override_at
            if hasattr(device, "manual_override_by") and device.manual_override_by:
                db_device.manual_override_by = device.manual_override_by
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
                active_defense_status=device.active_defense_status.value,
                first_seen=device.first_seen,
                last_seen=device.last_seen,
                tags=json.dumps(device.tags) if device.tags else None,
                alias=device.alias,
                vendor_guess=device.vendor_guess,
                model_guess=device.model_guess,
                recognition_confidence=device.recognition_confidence,
                discovery_source=getattr(device, "discovery_source", None),
                freshness_score=getattr(device, "freshness_score", None),
                recognition_evidence=(
                    json.dumps(device.recognition_evidence)
                    if device.recognition_evidence
                    else None
                ),
                manual_profile_id=getattr(device, "manual_profile_id", None),
                # Manual override fields (legacy; cleared when manual_profile_id is set)
                name_manual=(
                    None
                    if getattr(device, "manual_profile_id", None)
                    else getattr(device, "name_manual", None)
                ),
                vendor_manual=(
                    None
                    if getattr(device, "manual_profile_id", None)
                    else getattr(device, "vendor_manual", None)
                ),
                manual_override_at=getattr(device, "manual_override_at", None),
                manual_override_by=getattr(device, "manual_override_by", None),
            )
            self.session.add(db_device)

        await self.session.flush()
        if getattr(db_device, "manual_profile_id", None):
            try:
                await self.session.refresh(
                    db_device, attribute_names=["manual_profile"]
                )
            except Exception:
                logger.debug("Manual profile refresh skipped for %s", mac_lower)
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
        device_model.active_defense_status = device.active_defense_status.value
        device_model.last_seen = device.last_seen
        device_model.tags = json.dumps(device.tags) if device.tags else None
        device_model.alias = device.alias
        device_model.discovery_source = getattr(device, "discovery_source", None)
        device_model.freshness_score = getattr(device, "freshness_score", None)

        await self.session.flush()
        return self.to_domain_model(device_model)

    async def update_metadata(
        self,
        mac: str,
        *,
        alias: str | None | object = UNSET,
        tags: list[str] | None | object = UNSET,
    ) -> Device | None:
        """Update mutable display metadata.

        This keeps repository writes on ORM models instead of mutating domain objects
        as if they were SQLAlchemy rows.
        """
        result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.mac == mac.lower())
        )
        device_model = result.scalar_one_or_none()
        if not device_model:
            return None

        if alias is not UNSET:
            device_model.alias = alias
        if tags is not UNSET:
            device_model.tags = json.dumps(tags) if tags else None

        await self.session.flush()
        return self.to_domain_model(device_model)

    async def apply_recognition_override(
        self,
        mac: str,
        *,
        vendor: str | None,
        model: str | None,
        device_type: DeviceType | None,
        evidence: dict | None,
    ) -> Device | None:
        """Persist an operator-confirmed recognition override."""
        result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.mac == mac.lower())
        )
        device_model = result.scalar_one_or_none()
        if not device_model:
            return None

        if vendor is not None:
            device_model.vendor_guess = vendor
            device_model.vendor = vendor
        if model is not None:
            device_model.model_guess = model
            device_model.model = model
        if device_type is not None:
            device_model.type = DeviceTypeEnum(device_type.value)

        device_model.recognition_manual_override = True
        device_model.recognition_confidence = 100
        device_model.recognition_evidence = json.dumps(evidence) if evidence else None

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
        self, mac: str, status: ActiveDefenseStatus | str
    ) -> DeviceModel | None:
        """Update active defense status for a device."""
        status_value = status.value if hasattr(status, "value") else status
        result = await self.session.execute(
            update(DeviceModel)
            .where(DeviceModel.mac == mac.lower())
            .values(active_defense_status=status_value)
            .returning(DeviceModel)
        )
        await self.session.flush()
        return result.scalar_one_or_none()

    # Defense status methods removed in v2.0 (active defense refactor)
    # Use update_attack_status() instead

    async def update_manual_labels(
        self,
        mac: str,
        name_manual: str | None = None,
        vendor_manual: str | None = None,
        updated_by: str | None = None,
    ) -> DeviceModel | None:
        """Update manual labels for a device.

        Args:
            mac: Device MAC address
            name_manual: User-provided device name (None to clear)
            vendor_manual: User-provided vendor name (None to clear)
            updated_by: Username who made the update

        Returns:
            Updated DeviceModel or None if not found
        """
        result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.mac == mac.lower())
        )
        device_model = result.scalar_one_or_none()
        if not device_model:
            return None

        # Update manual override fields
        device_model.name_manual = name_manual
        device_model.vendor_manual = vendor_manual
        device_model.manual_override_at = datetime.now(UTC)
        device_model.manual_override_by = updated_by

        # Set the recognition_manual_override flag
        has_manual = bool(name_manual or vendor_manual)
        device_model.recognition_manual_override = has_manual

        await self.session.flush()
        return device_model

    async def bind_manual_profile(
        self,
        mac: str,
        profile_id: int,
        updated_by: str | None = None,
        manual_name: str | None = None,
        manual_vendor: str | None = None,
    ) -> DeviceModel | None:
        """Bind a device to a manual profile and clear legacy manual columns."""
        result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.mac == mac.lower())
        )
        device_model = result.scalar_one_or_none()
        if not device_model:
            return None

        device_model.manual_profile_id = profile_id
        device_model.name_manual = None
        device_model.vendor_manual = None
        device_model.manual_override_at = datetime.now(UTC)
        device_model.manual_override_by = updated_by
        device_model.recognition_manual_override = bool(manual_name or manual_vendor)
        await self.session.flush()
        try:
            await self.session.refresh(device_model, attribute_names=["manual_profile"])
        except Exception:
            logger.debug("Manual profile refresh skipped for %s", mac.lower())
        return device_model

    async def clear_manual_profile(
        self, mac: str, updated_by: str | None = None
    ) -> DeviceModel | None:
        """Unbind manual profile and clear manual flags on a device."""
        result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.mac == mac.lower())
        )
        device_model = result.scalar_one_or_none()
        if not device_model:
            return None

        device_model.manual_profile_id = None
        device_model.name_manual = None
        device_model.vendor_manual = None
        device_model.manual_override_at = datetime.now(UTC)
        device_model.manual_override_by = updated_by
        device_model.recognition_manual_override = False
        await self.session.flush()
        try:
            await self.session.refresh(device_model, attribute_names=["manual_profile"])
        except Exception:
            logger.debug("Manual profile clear refresh skipped for %s", mac.lower())
        return device_model

    def to_domain_model(self, device_model: DeviceModel) -> Device:
        """Convert database model to domain model."""
        manual_profile = (
            DeviceManualProfile.model_validate(device_model.manual_profile)
            if getattr(device_model, "manual_profile", None)
            else None
        )
        name_auto = device_model.name
        vendor_auto = device_model.vendor or device_model.vendor_guess
        display_name = (
            (manual_profile.manual_name if manual_profile else None)
            or device_model.name_manual
            or device_model.alias
            or name_auto
            or device_model.model
            or device_model.model_guess
        )
        display_vendor = (
            (manual_profile.manual_vendor if manual_profile else None)
            or device_model.vendor_manual
            or vendor_auto
            or device_model.vendor_guess
        )
        name_manual = (
            manual_profile.manual_name
            if manual_profile
            else getattr(device_model, "name_manual", None)
        )
        vendor_manual = (
            manual_profile.manual_vendor
            if manual_profile
            else getattr(device_model, "vendor_manual", None)
        )
        return Device(
            mac=device_model.mac,
            ip=device_model.ip,
            name=device_model.name,
            vendor=device_model.vendor,
            model=device_model.model,
            type=DeviceType(device_model.type.value),
            status=DeviceStatus(device_model.status.value),
            active_defense_status=ActiveDefenseStatus(
                device_model.active_defense_status
            ),
            first_seen=device_model.first_seen,
            last_seen=device_model.last_seen,
            tags=json.loads(device_model.tags) if device_model.tags else [],
            alias=device_model.alias,
            manual_profile_id=getattr(device_model, "manual_profile_id", None),
            manual_profile=manual_profile,
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
            name_manual=name_manual,
            vendor_manual=vendor_manual,
            manual_override_at=getattr(device_model, "manual_override_at", None),
            manual_override_by=getattr(device_model, "manual_override_by", None),
            discovery_source=getattr(device_model, "discovery_source", None),
            freshness_score=getattr(device_model, "freshness_score", None),
            display_name=display_name,
            display_vendor=display_vendor,
            name_auto=name_auto,
            vendor_auto=vendor_auto,
        )


# Dependency injection for FastAPI
def get_device_repository(session: AsyncSession) -> DeviceRepository:
    """Get device repository instance."""
    return DeviceRepository(session)
