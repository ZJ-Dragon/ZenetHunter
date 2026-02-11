"""MACVendors provider for vendor lookup (no API key required)."""

import logging
from typing import Any

from app.core.config import get_settings
from app.services.recognition.providers.base import RecognitionProvider
from app.services.recognition.providers.cache import get_recognition_cache
from app.services.recognition.providers.http_client import (
    create_http_client_for_provider,
)

logger = logging.getLogger(__name__)


class MACVendorsProvider(RecognitionProvider):
    """
    MACVendors.com provider for vendor lookup.

    Public API: https://macvendors.com/api
    - No registration or API key required
    - Free tier: up to 1,000 requests/day
    - Rate limit: ~1 request/second recommended
    - Privacy: Only sends OUI (first 3 octets of MAC), not full MAC
    """

    def __init__(self):
        """Initialize MACVendors provider."""
        self.settings = get_settings()
        self.cache = get_recognition_cache()
        self._http_client = None
        self._enabled = False

    @property
    def name(self) -> str:
        """Provider name."""
        return "macvendors"

    @property
    def requires_key(self) -> bool:
        """MACVendors does not require an API key."""
        return False

    @property
    def privacy_level(self) -> str:
        """Privacy level: low (only OUI sent, not full MAC)."""
        return "low"

    def is_enabled(self) -> bool:
        """Check if provider is enabled."""
        # Check global external lookup flag
        if not getattr(self.settings, "feature_external_lookup", False):
            return False
        # MACVendors is always available if external lookup is enabled
        return True

    def _extract_oui(self, mac: str) -> str:
        """
        Extract OUI (first 3 octets) from MAC address.

        Args:
            mac: MAC address (any format)

        Returns:
            OUI in format "XX:XX:XX" or empty string if invalid
        """
        # Normalize MAC: remove separators, uppercase
        mac_clean = mac.replace(":", "").replace("-", "").upper()
        if len(mac_clean) < 6:
            return ""

        # Extract first 6 hex digits (3 octets)
        oui_hex = mac_clean[:6]
        # Format as XX:XX:XX
        return f"{oui_hex[0:2]}:{oui_hex[2:4]}:{oui_hex[4:6]}"

    async def _get_http_client(self):
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = create_http_client_for_provider("macvendors")
        return self._http_client

    async def lookup_vendor(self, oui: str) -> dict[str, Any] | None:
        """
        Lookup vendor from OUI.

        Args:
            oui: OUI prefix (e.g., "00:11:22" or full MAC "00:11:22:33:44:55")

        Returns:
            Dictionary with vendor, confidence, source or None
        """
        if not self.is_enabled():
            logger.debug("MACVendors provider is disabled")
            return None

        # Extract OUI if full MAC provided
        if len(oui.replace(":", "").replace("-", "")) > 6:
            oui = self._extract_oui(oui)
            if not oui:
                return None

        # Normalize OUI format
        oui_normalized = oui.replace("-", ":").upper()

        # Check cache first
        cached = self.cache.get(self.name, oui_normalized)
        if cached is not None:
            logger.debug(f"Cache hit for OUI {oui_normalized}")
            # Audit log (cache hit)
            self._audit_log("vendor", True, cache_hit=True)
            return cached

        try:
            # Make API request
            client = await self._get_http_client()
            # MACVendors API: https://api.macvendors.com/{OUI}
            url = f"https://api.macvendors.com/{oui_normalized.replace(':', '')}"

            response = await client.get(url)
            vendor_name = response.text.strip()

            # MACVendors returns vendor name or empty string
            if not vendor_name or vendor_name.startswith("Not found"):
                logger.debug(f"Vendor not found for OUI {oui_normalized}")
                # Cache negative result (shorter TTL handled by cache)
                result = None
                # Audit log (not found)
                self._audit_log("vendor", True, cache_hit=False)
            else:
                result = {
                    "vendor": vendor_name,
                    "confidence": 80,  # High confidence for OUI match
                    "source": f"external:{self.name}",
                }
                logger.info(f"MACVendors lookup: {oui_normalized} -> {vendor_name}")
                # Audit log (success)
                self._audit_log("vendor", True, cache_hit=False)

            # Cache result
            self.cache.set(self.name, oui_normalized, result)
            return result

        except Exception as e:
            logger.warning(f"MACVendors lookup failed for {oui_normalized}: {e}")
            # Audit log (error)
            self._audit_log("vendor", False, cache_hit=False, error=str(e)[:100])
            # Don't cache errors (allow retry)
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

    async def lookup_device(self, fingerprint: dict[str, Any]) -> dict[str, Any] | None:
        """
        MACVendors does not support device fingerprint lookup.

        Returns:
            None (not supported)
        """
        return None

    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.close()
            self._http_client = None
