"""Fingerbank provider for device fingerprint lookup (requires API key)."""

import logging
from typing import Any

from app.core.config import get_settings
from app.services.recognition.providers.base import RecognitionProvider
from app.services.recognition.providers.cache import get_recognition_cache
from app.services.recognition.providers.http_client import (
    create_http_client_for_provider,
)

logger = logging.getLogger(__name__)


class FingerbankProvider(RecognitionProvider):
    """
    Fingerbank provider for device fingerprint lookup.

    API: https://api.fingerbank.org
    - Requires API key (registration at https://fingerbank.org)
    - Provides detailed device model/category identification
    - Privacy: Sends combined fingerprint (higher privacy risk)
    - Default: Disabled (requires explicit key configuration)
    """

    def __init__(self):
        """Initialize Fingerbank provider."""
        self.settings = get_settings()
        self.cache = get_recognition_cache()
        self._http_client = None
        self.api_key = getattr(self.settings, "fingerbank_api_key", None)

    @property
    def name(self) -> str:
        """Provider name."""
        return "fingerbank"

    @property
    def requires_key(self) -> bool:
        """Fingerbank requires an API key."""
        return True

    @property
    def privacy_level(self) -> str:
        """Privacy level: high (sends full fingerprint)."""
        return "high"

    def is_enabled(self) -> bool:
        """Check if provider is enabled and configured."""
        # Check global external lookup flag
        if not getattr(self.settings, "feature_external_lookup", False):
            return False
        # Check API key
        if not self.api_key:
            return False
        return True

    async def _get_http_client(self):
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = create_http_client_for_provider("fingerbank")
        return self._http_client

    async def lookup_vendor(self, oui: str) -> dict[str, Any] | None:
        """
        Fingerbank does not provide simple vendor lookup.

        Use lookup_device() for fingerprint-based identification.

        Returns:
            None (not supported)
        """
        return None

    async def lookup_device(self, fingerprint: dict[str, Any]) -> dict[str, Any] | None:
        """
        Lookup device from fingerprint.

        Args:
            fingerprint: Dictionary with device fingerprint signals

        Returns:
            Dictionary with vendor, model, category, confidence, source or None
        """
        if not self.is_enabled():
            logger.debug("Fingerbank provider is disabled or not configured")
            return None

        # Create fingerprint hash for cache key
        import hashlib
        import json

        fp_str = json.dumps(fingerprint, sort_keys=True)
        fp_hash = hashlib.sha256(fp_str.encode()).hexdigest()[:16]

        # Check cache
        cached = self.cache.get(self.name, fp_hash)
        if cached is not None:
            logger.debug(f"Cache hit for fingerprint {fp_hash}")
            # Audit log (cache hit)
            self._audit_log("device", True, cache_hit=True)
            return cached

        try:
            # Make API request
            # Note: Fingerbank API format may vary - this is a placeholder
            # Actual implementation should follow Fingerbank API documentation
            client = await self._get_http_client()
            url = "https://api.fingerbank.org/api/v2/combinations/interrogate"

            # Prepare fingerprint payload (sanitized)
            payload = {
                "dhcp_fingerprint": fingerprint.get("dhcp_opt55_prl"),
                "dhcp_vendor": fingerprint.get("dhcp_opt60_vci"),
                "user_agent": fingerprint.get("user_agent"),
            }

            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            }

            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

            # Parse Fingerbank response (format depends on API version)
            if data and "device" in data:
                device_info = data["device"]
                result = {
                    "vendor": device_info.get("manufacturer"),
                    "model": device_info.get("name"),
                    "category": device_info.get("category"),
                    "confidence": min(100, int(device_info.get("score", 0) * 100)),
                    "source": f"external:{self.name}",
                }
                logger.info(
                    f"Fingerbank lookup: {fp_hash} -> "
                    f"{result.get('vendor')}/{result.get('model')}"
                )
                # Audit log (success)
                self._audit_log("device", True, cache_hit=False)
            else:
                result = None
                # Audit log (not found)
                self._audit_log("device", True, cache_hit=False)

            # Cache result
            self.cache.set(self.name, fp_hash, result)
            return result

        except Exception as e:
            logger.warning(f"Fingerbank lookup failed for fingerprint {fp_hash}: {e}")
            # Audit log (error)
            self._audit_log("device", False, cache_hit=False, error=str(e)[:100])
            # Don't cache errors
            return None

    def _audit_log(
        self,
        query_type: str,
        success: bool,
        cache_hit: bool = False,
        error: str | None = None,
    ):
        """Log external lookup to audit trail (sanitized)."""
        from app.services.recognition.external_service_policy import (
            get_external_service_policy,
        )

        policy = get_external_service_policy()
        if policy.should_audit():
            audit_entry = policy.create_audit_entry(
                provider=self.name,
                query_type=query_type,
                success=success,
                cache_hit=cache_hit,
                error=error,
            )
            # Log to structured logger (sanitized, no sensitive data)
            logger.info(
                "External recognition lookup",
                extra={
                    "audit": audit_entry,
                    "provider": self.name,
                    "query_type": query_type,
                },
            )

    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.close()
            self._http_client = None
