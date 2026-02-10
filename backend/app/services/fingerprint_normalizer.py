"""Fingerprint normalizer for standardizing device recognition signals."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class FingerprintNormalizer:
    """Normalizes fingerprint signals for stable matching."""

    @staticmethod
    def normalize_hostname(hostname: str | None) -> str | None:
        """
        Normalize DHCP Option 12 (Host Name).

        Args:
            hostname: Raw hostname string

        Returns:
            Normalized hostname (lowercase, trimmed) or None
        """
        if not hostname:
            return None
        # Lowercase and strip whitespace
        normalized = hostname.strip().lower()
        # Remove trailing dots (common in FQDN)
        normalized = normalized.rstrip(".")
        return normalized if normalized else None

    @staticmethod
    def normalize_opt55_prl(prl: str | list[int] | None) -> str | None:
        """
        Normalize DHCP Option 55 (Parameter Request List).

        RFC 2132: Option 55 is a list of requested option codes.

        Args:
            prl: Parameter Request List as string (comma-separated) or list of ints

        Returns:
            Normalized PRL as comma-separated sorted integers, or None
        """
        if not prl:
            return None

        # Convert to list of integers
        if isinstance(prl, str):
            # Handle comma-separated or space-separated
            parts = prl.replace(",", " ").split()
            try:
                int_list = sorted([int(p.strip()) for p in parts if p.strip()])
            except (ValueError, TypeError):
                logger.warning(f"Invalid PRL format: {prl}")
                return None
        elif isinstance(prl, list):
            try:
                int_list = sorted([int(x) for x in prl if x is not None])
            except (ValueError, TypeError):
                logger.warning(f"Invalid PRL list: {prl}")
                return None
        else:
            return None

        if not int_list:
            return None

        # Return as comma-separated string of sorted integers
        return ",".join(str(x) for x in int_list)

    @staticmethod
    def normalize_opt60_vci(vci: str | None) -> str | None:
        """
        Normalize DHCP Option 60 (Vendor Class Identifier).

        RFC 2132: Option 60 contains vendor-specific information.

        Args:
            vci: Vendor Class Identifier string

        Returns:
            Normalized VCI (trimmed, case-preserved but deduplicated) or None
        """
        if not vci:
            return None
        # Strip whitespace but preserve case (VCI is case-sensitive per RFC)
        normalized = vci.strip()
        # Remove null bytes if present
        normalized = normalized.replace("\x00", "")
        return normalized if normalized else None

    @staticmethod
    def normalize_user_agent(ua: str | None) -> str | None:
        """
        Normalize User-Agent string.

        Args:
            ua: Raw User-Agent string

        Returns:
            Normalized UA (trimmed) or None
        """
        if not ua:
            return None
        # Strip whitespace
        normalized = ua.strip()
        # Limit length to prevent DB overflow (typical UA is < 512 chars)
        if len(normalized) > 512:
            normalized = normalized[:512]
        return normalized if normalized else None

    @staticmethod
    def normalize_ja3(ja3: str | None) -> str | None:
        """
        Normalize JA3 TLS fingerprint.

        JA3 format: md5 hash of TLS ClientHello fields.

        Args:
            ja3: JA3 hash string (32 hex chars for MD5)

        Returns:
            Normalized JA3 (lowercase, trimmed) or None
        """
        if not ja3:
            return None
        # JA3 is typically a 32-character hex string (MD5)
        normalized = ja3.strip().lower()
        # Validate format (optional, but helpful)
        if len(normalized) == 32 and all(c in "0123456789abcdef" for c in normalized):
            return normalized
        # Allow non-standard formats but still normalize
        return normalized if normalized else None

    @staticmethod
    def normalize_fingerprint(fingerprint_data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize all fingerprint fields in a dictionary.

        Args:
            fingerprint_data: Dictionary with fingerprint fields

        Returns:
            Dictionary with normalized fields
        """
        normalized = {}

        if "dhcp_opt12_hostname" in fingerprint_data:
            normalized["dhcp_opt12_hostname"] = (
                FingerprintNormalizer.normalize_hostname(
                    fingerprint_data["dhcp_opt12_hostname"]
                )
            )

        if "dhcp_opt55_prl" in fingerprint_data:
            normalized["dhcp_opt55_prl"] = FingerprintNormalizer.normalize_opt55_prl(
                fingerprint_data["dhcp_opt55_prl"]
            )

        if "dhcp_opt60_vci" in fingerprint_data:
            normalized["dhcp_opt60_vci"] = FingerprintNormalizer.normalize_opt60_vci(
                fingerprint_data["dhcp_opt60_vci"]
            )

        if "user_agent" in fingerprint_data:
            normalized["user_agent"] = FingerprintNormalizer.normalize_user_agent(
                fingerprint_data["user_agent"]
            )

        if "ja3" in fingerprint_data:
            normalized["ja3"] = FingerprintNormalizer.normalize_ja3(
                fingerprint_data["ja3"]
            )

        # Pass through other fields (mdns_services, ssdp_server, evidence, active_probe fields)
        # These are JSON or structured data and will be handled separately
        pass_through_keys = (
            "mdns_services",
            "ssdp_server",
            "ssdp_manufacturer",
            "ssdp_model",
            "ssdp_model_name",
            "evidence",
            # Active probe fields
            "http_server",
            "http_title",
            "http_meta_device",
            "http_meta_model",
            "http_meta_product",
            "telnet_banner",
            "ssh_banner",
            "ssh_vendor",
            "printer_protocol",
            "iot_protocol",
        )
        for key in pass_through_keys:
            if key in fingerprint_data:
                normalized[key] = fingerprint_data[key]

        return normalized

    @staticmethod
    def compute_fingerprint_key(fingerprint_data: dict[str, Any]) -> str:
        """
        Compute a stable fingerprint key for matching.

        Combines key signals into a hashable string for lookup.

        Args:
            fingerprint_data: Dictionary with fingerprint fields

        Returns:
            Fingerprint key string (for use in matching/caching)
        """
        parts = []

        # Add normalized DHCP signals
        if fingerprint_data.get("dhcp_opt55_prl"):
            parts.append(f"prl:{fingerprint_data['dhcp_opt55_prl']}")
        if fingerprint_data.get("dhcp_opt60_vci"):
            parts.append(f"vci:{fingerprint_data['dhcp_opt60_vci']}")
        if fingerprint_data.get("dhcp_opt12_hostname"):
            parts.append(f"host:{fingerprint_data['dhcp_opt12_hostname']}")

        # Add optional signals (lower weight)
        if fingerprint_data.get("ja3"):
            parts.append(f"ja3:{fingerprint_data['ja3']}")

        if not parts:
            return "empty"

        # Sort parts for consistent key generation
        return "|".join(sorted(parts))


# Global singleton instance
_normalizer_instance: FingerprintNormalizer | None = None


def get_fingerprint_normalizer() -> FingerprintNormalizer:
    """Get the global FingerprintNormalizer instance."""
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = FingerprintNormalizer()
    return _normalizer_instance
