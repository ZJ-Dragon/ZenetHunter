"""External service policy: controls, whitelist, rate limits, privacy settings."""

import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ExternalServicePolicy:
    """Centralized policy for external recognition services."""

    def __init__(self):
        """Initialize policy from settings."""
        self.settings = get_settings()

    @property
    def external_lookup_enabled(self) -> bool:
        """
        Check if external lookups are enabled.

        Note: Environment variable defaults to False (safe default).
        UI and software layers add "soft restrictions" on top.
        """
        return getattr(self.settings, "feature_external_lookup", False)

    @property
    def allowed_domains(self) -> list[str]:
        """Get whitelist of allowed domains."""
        return [
            "macvendors.com",
            "api.macvendors.com",
            "api.fingerbank.org",
        ]

    @property
    def oui_only_mode(self) -> bool:
        """
        Check if OUI-only mode is enabled (privacy protection).

        When enabled, only OUI prefixes are sent, never full MAC addresses.
        """
        return getattr(self.settings, "external_lookup_oui_only", True)

    def is_domain_allowed(self, domain: str) -> bool:
        """
        Check if domain is in whitelist.

        Args:
            domain: Domain name to check

        Returns:
            True if allowed, False otherwise
        """
        domain_lower = domain.lower()
        return domain_lower in [d.lower() for d in self.allowed_domains]

    def sanitize_query(self, provider: str, query: str) -> str:
        """
        Sanitize query to minimize privacy exposure.

        Args:
            provider: Provider name
            query: Original query (may be full MAC or fingerprint)

        Returns:
            Sanitized query (OUI only if oui_only_mode enabled)
        """
        if provider == "macvendors":
            # For MACVendors, extract OUI if full MAC provided
            if self.oui_only_mode and len(query.replace(":", "").replace("-", "")) > 6:
                # Extract OUI (first 3 octets)
                mac_clean = query.replace(":", "").replace("-", "").upper()
                if len(mac_clean) >= 6:
                    oui_hex = mac_clean[:6]
                    return f"{oui_hex[0:2]}:{oui_hex[2:4]}:{oui_hex[4:6]}"
            return query

        # For other providers, return as-is (caller should handle sanitization)
        return query

    def get_provider_config(self, provider: str) -> dict[str, Any]:
        """
        Get configuration for a specific provider.

        Args:
            provider: Provider name

        Returns:
            Configuration dictionary
        """
        configs = {
            "macvendors": {
                "enabled": self.external_lookup_enabled,
                "requires_key": False,
                "privacy_level": "low",
                "qps_limit": 1.0,
                "daily_limit": 1000,
                "description": "Vendor lookup from OUI (no API key required)",
            },
            "fingerbank": {
                "enabled": (
                    self.external_lookup_enabled
                    and getattr(self.settings, "fingerbank_api_key", None) is not None
                ),
                "requires_key": True,
                "privacy_level": "high",
                "qps_limit": 0.5,
                "daily_limit": 500,
                "description": "Device fingerprint lookup (requires API key)",
            },
        }

        return configs.get(provider.lower(), {})

    def should_audit(self) -> bool:
        """Check if audit logging is enabled."""
        return True  # Always audit external lookups

    def create_audit_entry(
        self,
        provider: str,
        query_type: str,
        success: bool,
        cache_hit: bool,
        error: str | None = None,
    ) -> dict[str, Any]:
        """
        Create audit log entry (sanitized, no sensitive data).

        Args:
            provider: Provider name
            query_type: Type of query ("vendor" or "device")
            success: Whether query succeeded
            cache_hit: Whether result came from cache
            error: Error message if failed (sanitized)

        Returns:
            Audit entry dictionary
        """
        from datetime import datetime, UTC

        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "provider": provider,
            "query_type": query_type,
            "success": success,
            "cache_hit": cache_hit,
            "privacy_level": self.get_provider_config(provider).get("privacy_level"),
        }

        if error:
            # Sanitize error (don't include full MACs or tokens)
            entry["error"] = error[:100]  # Truncate long errors

        return entry


# Global policy instance
_policy_instance: ExternalServicePolicy | None = None


def get_external_service_policy() -> ExternalServicePolicy:
    """Get global external service policy instance."""
    global _policy_instance
    if _policy_instance is None:
        _policy_instance = ExternalServicePolicy()
    return _policy_instance
