"""Base interface for external recognition providers."""

from abc import ABC, abstractmethod
from typing import Any


class RecognitionProvider(ABC):
    """Base interface for external device recognition providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        pass

    @property
    @abstractmethod
    def requires_key(self) -> bool:
        """Whether this provider requires an API key."""
        pass

    @property
    @abstractmethod
    def privacy_level(self) -> str:
        """Privacy level: 'low' (OUI only) or 'high' (full fingerprint)."""
        pass

    @abstractmethod
    async def lookup_vendor(self, oui: str) -> dict[str, Any] | None:
        """
        Lookup vendor from OUI (Organizationally Unique Identifier).

        Args:
            oui: OUI prefix (e.g., "00:11:22" or "001122")

        Returns:
            Dictionary with:
                - vendor: Vendor name (str)
                - confidence: Confidence score 0-100 (int)
                - source: Provider name (str)
            Or None if not found/error
        """
        pass

    @abstractmethod
    async def lookup_device(self, fingerprint: dict[str, Any]) -> dict[str, Any] | None:
        """
        Lookup device model/category from fingerprint (optional, requires key).

        Args:
            fingerprint: Dictionary with device fingerprint signals

        Returns:
            Dictionary with:
                - vendor: Vendor name (str, optional)
                - model: Model name (str, optional)
                - category: Device category (str, optional)
                - confidence: Confidence score 0-100 (int)
                - source: Provider name (str)
            Or None if not found/error/not supported
        """
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if provider is enabled and configured."""
        pass
