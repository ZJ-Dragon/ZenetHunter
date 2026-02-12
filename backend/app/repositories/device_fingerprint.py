"""Device fingerprint repository for database operations."""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.device_fingerprint import DeviceFingerprintModel


class DeviceFingerprintRepository:
    """Repository for device fingerprint database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_mac(self, mac: str) -> DeviceFingerprintModel | None:
        """Get fingerprint by device MAC address."""
        result = await self.session.execute(
            select(DeviceFingerprintModel).where(
                DeviceFingerprintModel.device_mac == mac.lower()
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self, mac: str, fingerprint_data: dict[str, Any]
    ) -> DeviceFingerprintModel:
        """Insert or update device fingerprint."""
        mac_lower = mac.lower()
        result = await self.session.execute(
            select(DeviceFingerprintModel).where(
                DeviceFingerprintModel.device_mac == mac_lower
            )
        )
        db_fingerprint = result.scalar_one_or_none()

        if db_fingerprint:
            # Update existing fingerprint
            for key, value in fingerprint_data.items():
                if hasattr(db_fingerprint, key):
                    if key in (
                        "mdns_services",
                        "ssdp_server",
                        "evidence",
                    ) and isinstance(value, (dict, list)):
                        # JSON serialize for complex fields
                        setattr(
                            db_fingerprint, key, json.dumps(value) if value else None
                        )
                    else:
                        setattr(db_fingerprint, key, value)
            db_fingerprint.last_updated = datetime.now(UTC)
        else:
            # Create new fingerprint
            # Handle JSON serialization for complex fields
            mdns_services = (
                json.dumps(fingerprint_data.get("mdns_services"))
                if fingerprint_data.get("mdns_services")
                else None
            )
            ssdp_server = (
                json.dumps(fingerprint_data.get("ssdp_server"))
                if fingerprint_data.get("ssdp_server")
                else None
            )
            evidence = (
                json.dumps(fingerprint_data.get("evidence"))
                if fingerprint_data.get("evidence")
                else None
            )

            db_fingerprint = DeviceFingerprintModel(
                device_mac=mac_lower,
                dhcp_opt12_hostname=fingerprint_data.get("dhcp_opt12_hostname"),
                dhcp_opt55_prl=fingerprint_data.get("dhcp_opt55_prl"),
                dhcp_opt60_vci=fingerprint_data.get("dhcp_opt60_vci"),
                user_agent=fingerprint_data.get("user_agent"),
                mdns_services=mdns_services,
                ssdp_server=ssdp_server,
                ja3=fingerprint_data.get("ja3"),
                best_guess_vendor=fingerprint_data.get("best_guess_vendor"),
                best_guess_model=fingerprint_data.get("best_guess_model"),
                confidence=fingerprint_data.get("confidence"),
                evidence=evidence,
                first_seen=datetime.now(UTC),
                last_updated=datetime.now(UTC),
            )
            self.session.add(db_fingerprint)

        await self.session.flush()
        return db_fingerprint

    async def delete(self, mac: str) -> bool:
        """Delete fingerprint by device MAC address."""
        result = await self.session.execute(
            select(DeviceFingerprintModel).where(
                DeviceFingerprintModel.device_mac == mac.lower()
            )
        )
        fingerprint = result.scalar_one_or_none()
        if not fingerprint:
            return False

        await self.session.delete(fingerprint)
        await self.session.flush()
        return True


# Dependency injection for FastAPI
def get_device_fingerprint_repository(
    session: AsyncSession,
) -> DeviceFingerprintRepository:
    """Get device fingerprint repository instance."""
    return DeviceFingerprintRepository(session)
