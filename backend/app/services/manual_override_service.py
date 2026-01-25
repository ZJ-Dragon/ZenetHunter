"""Manual Override Service for applying user labels during scanning.

This service checks if a device's fingerprint matches any stored manual
overrides and applies the user-provided labels automatically.
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.manual_override import ManualOverrideModel
from app.repositories.manual_override import ManualOverrideRepository
from app.services.fingerprint_key import generate_fingerprint_key

logger = logging.getLogger(__name__)


class ManualOverrideService:
    """Service for managing and applying manual device overrides."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ManualOverrideRepository(session)

    async def check_and_apply_override(
        self,
        mac: str,
        fingerprint_data: dict[str, Any] | None = None,
        vendor_guess: str | None = None,
        model_guess: str | None = None,
    ) -> dict[str, Any] | None:
        """Check if device matches a manual override and return labels if found.

        This method generates a fingerprint key from the device's characteristics
        and checks if there's a matching manual override in the database.

        Args:
            mac: Device MAC address
            fingerprint_data: Dict containing fingerprint signals
            vendor_guess: Auto-detected vendor
            model_guess: Auto-detected model

        Returns:
            Dict with manual labels if match found:
                - name_manual: User-provided name
                - vendor_manual: User-provided vendor
                - fingerprint_key: The matching key
                - source_mac: Original device that created this override
            Or None if no match
        """
        # Generate fingerprint key for this device
        fingerprint_key, components = generate_fingerprint_key(
            fingerprint_data=fingerprint_data,
            mac=mac,
            vendor_guess=vendor_guess,
            model_guess=model_guess,
        )

        # Look up in manual override table
        override = await self.repo.get_by_fingerprint_key(fingerprint_key)

        if override:
            # Found a match - increment counter and return labels
            await self.repo.increment_match_count(fingerprint_key)

            logger.info(
                f"Manual override matched for {mac}: "
                f"key={fingerprint_key}, name={override.manual_name}, "
                f"vendor={override.manual_vendor}"
            )

            return {
                "name_manual": override.manual_name,
                "vendor_manual": override.manual_vendor,
                "fingerprint_key": fingerprint_key,
                "source_mac": override.source_mac,
                "match_count": override.match_count + 1,
            }

        logger.debug(f"No manual override found for {mac} (key={fingerprint_key})")
        return None

    async def get_override_for_key(
        self, fingerprint_key: str
    ) -> ManualOverrideModel | None:
        """Get manual override by fingerprint key.

        Args:
            fingerprint_key: The fingerprint key to look up

        Returns:
            ManualOverrideModel if found, None otherwise
        """
        return await self.repo.get_by_fingerprint_key(fingerprint_key)

    async def list_all_overrides(self) -> list[ManualOverrideModel]:
        """List all manual overrides.

        Returns:
            List of all ManualOverrideModel entries
        """
        return await self.repo.get_all()


async def apply_manual_override_to_device(
    session: AsyncSession,
    device_mac: str,
    fingerprint_data: dict[str, Any] | None = None,
    vendor_guess: str | None = None,
    model_guess: str | None = None,
) -> dict[str, Any] | None:
    """Convenience function to check and apply manual override.

    Args:
        session: Database session
        device_mac: Device MAC address
        fingerprint_data: Device fingerprint data
        vendor_guess: Auto-detected vendor
        model_guess: Auto-detected model

    Returns:
        Dict with manual labels if match found, None otherwise
    """
    service = ManualOverrideService(session)
    return await service.check_and_apply_override(
        mac=device_mac,
        fingerprint_data=fingerprint_data,
        vendor_guess=vendor_guess,
        model_guess=model_guess,
    )
