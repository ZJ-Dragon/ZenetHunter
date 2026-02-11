"""Recognition provider endpoints and settings."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.core.security import get_current_admin
from app.models.auth import User
from app.services.recognition.external_service_policy import get_external_service_policy
from app.services.recognition.providers.fingerbank import FingerbankProvider
from app.services.recognition.providers.macvendors import MACVendorsProvider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recognition", tags=["Recognition"])


@router.get("/providers")
async def get_providers() -> dict:
    """
    Get list of available recognition providers and their status.

    Returns:
        Dictionary with provider information:
        - providers: List of provider objects with name, enabled, requires_key, etc.
        - external_lookup_enabled: Global external lookup flag
    """
    policy = get_external_service_policy()

    providers = []

    # MACVendors provider
    macvendors = MACVendorsProvider()
    macvendors_config = policy.get_provider_config("macvendors")
    providers.append(
        {
            "name": "macvendors",
            "enabled": macvendors.is_enabled(),
            "requires_key": macvendors.requires_key,
            "privacy_level": macvendors.privacy_level,
            "qps_limit": macvendors_config.get("qps_limit"),
            "daily_limit": macvendors_config.get("daily_limit"),
            "description": macvendors_config.get("description"),
        }
    )

    # Fingerbank provider
    fingerbank = FingerbankProvider()
    fingerbank_config = policy.get_provider_config("fingerbank")
    providers.append(
        {
            "name": "fingerbank",
            "enabled": fingerbank.is_enabled(),
            "requires_key": fingerbank.requires_key,
            "privacy_level": fingerbank.privacy_level,
            "qps_limit": fingerbank_config.get("qps_limit"),
            "daily_limit": fingerbank_config.get("daily_limit"),
            "description": fingerbank_config.get("description"),
            "has_key": fingerbank.api_key is not None,
        }
    )

    return {
        "providers": providers,
        "external_lookup_enabled": policy.external_lookup_enabled,
        "oui_only_mode": policy.oui_only_mode,
    }


@router.post("/settings/external-lookup")
async def update_external_lookup_setting(
    enabled: bool,
    current_user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    """
    Enable or disable external recognition lookups.

    ⚠️  ADMIN ONLY - Requires administrator authentication.

    Args:
        enabled: True to enable external lookups, False to disable

    Returns:
        Dictionary with updated status

    Note:
        This endpoint updates the runtime setting but does not persist
        to environment variables. To make changes permanent, update
        FEATURE_EXTERNAL_LOOKUP environment variable and restart the service.
    """
    settings = get_settings()

    # Update setting (runtime only, not persisted)
    # Note: In production, you might want to persist this to a database
    # For now, we just update the settings object
    settings.feature_external_lookup = enabled

    logger.info(
        f"External lookup setting updated by {current_user.username}: {enabled}"
    )

    return {
        "external_lookup_enabled": enabled,
        "message": (
            "Setting updated (runtime only). "
            "To persist, set FEATURE_EXTERNAL_LOOKUP environment variable."
        ),
    }
