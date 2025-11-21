"""Abstract base class for switch management."""

from abc import ABC, abstractmethod


class SwitchManager(ABC):
    """
    Interface for managing managed switches (L2/L3).
    Used for features like DAI (Dynamic ARP Inspection) and DHCP Snooping.
    """

    @abstractmethod
    async def check_dai_capability(self) -> bool:
        """Check if the switch supports DAI."""
        pass

    @abstractmethod
    async def enable_dai(self, vlan_id: int = 1) -> bool:
        """Enable Dynamic ARP Inspection on a VLAN."""
        pass

    @abstractmethod
    async def bind_ip_mac(self, ip: str, mac: str, port: str) -> bool:
        """Create a static IP source binding (IP Source Guard / ARP ACL)."""
        pass
