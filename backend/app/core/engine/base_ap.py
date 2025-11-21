"""Access Point / Wireless Controller Management Interface."""

from abc import ABC, abstractmethod
from typing import Any

from app.models.wpa3 import Wpa3Config


class AccessPointManager(ABC):
    """
    Interface for managing wireless access points and 802.1X configuration.
    Supports WPA3-Personal/Enterprise and RADIUS integration.
    """

    @abstractmethod
    async def check_capabilities(self) -> bool:
        """Check if the AP supports WPA3/802.1X."""
        pass

    @abstractmethod
    async def configure_wpa3(
        self, config: Wpa3Config, params: dict[str, Any] | None = None
    ) -> bool:
        """
        Configure WPA3 security on the access point.
        
        Args:
            config: WPA3 configuration (mode, SSID, RADIUS, etc.)
            params: Additional device-specific parameters
            
        Returns:
            True if configuration succeeded
        """
        pass

    @abstractmethod
    async def assign_vlan(
        self, mac: str, vlan_id: int, port: str | None = None
    ) -> bool:
        """
        Assign a device to a specific VLAN after 802.1X authentication.
        
        Args:
            mac: Device MAC address
            vlan_id: Target VLAN ID
            port: Physical port (if applicable)
            
        Returns:
            True if assignment succeeded
        """
        pass

    @abstractmethod
    async def remove_vlan_assignment(self, mac: str) -> bool:
        """Remove VLAN assignment for a device."""
        pass

