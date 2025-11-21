"""DNS RPZ / Sinkhole Engine."""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DnsRpzEngine(ABC):
    """
    Interface for managing DNS Response Policy Zones (RPZ).
    Integrates with local DNS resolvers like BIND, Unbound, or Dnsmasq (via ipset/nftset).
    """

    @abstractmethod
    async def add_zone(self, zone_name: str, action: str = "NXDOMAIN") -> bool:
        """Add a new policy zone."""
        pass

    @abstractmethod
    async def add_rule(self, domain: str, action: str = "NXDOMAIN") -> bool:
        """Block or redirect a domain."""
        pass

    @abstractmethod
    async def remove_rule(self, domain: str) -> bool:
        """Remove a rule for a domain."""
        pass


class DummyDnsRpzEngine(DnsRpzEngine):
    """Dummy implementation for non-root/dev environments."""

    async def add_zone(self, zone_name: str, action: str = "NXDOMAIN") -> bool:
        logger.info(f"[DummyDNS] Added zone {zone_name} with action {action}")
        return True

    async def add_rule(self, domain: str, action: str = "NXDOMAIN") -> bool:
        logger.info(f"[DummyDNS] Blocking domain {domain} -> {action}")
        return True

    async def remove_rule(self, domain: str) -> bool:
        logger.info(f"[DummyDNS] Unblocking domain {domain}")
        return True
