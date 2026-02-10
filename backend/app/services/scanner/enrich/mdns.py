"""mDNS/DNS-SD enrichment for device fingerprinting (Stage B)."""

import asyncio
import logging
import socket
from typing import Any

logger = logging.getLogger(__name__)


class MDNSEnricher:
    """mDNS/DNS-SD enrichment to gather device service information."""

    def __init__(self, timeout: float = 3.0):
        """
        Initialize mDNS enricher.

        Args:
            timeout: Timeout for mDNS queries in seconds
        """
        self.timeout = timeout
        self.mdns_multicast = ("224.0.0.251", 5353)  # mDNS multicast address

    async def enrich_device(self, device_ip: str, device_mac: str) -> dict[str, Any]:
        """
        Enrich device fingerprint using mDNS queries.

        Args:
            device_ip: Device IP address
            device_mac: Device MAC address

        Returns:
            Dictionary with fingerprint data (mdns_services, hostname, etc.)
        """
        fingerprint: dict[str, Any] = {}
        services: list[str] = []
        hostname: str | None = None

        try:
            # Try using zeroconf library if available
            try:
                from zeroconf.asyncio import AsyncZeroconf

                # Use AsyncZeroconf for async operations
                async with AsyncZeroconf() as azc:
                    # Query for common services
                    service_types = [
                        "_http._tcp.local.",
                        "_https._tcp.local.",
                        "_ssh._tcp.local.",
                        "_printer._tcp.local.",
                        "_airplay._tcp.local.",
                        "_raop._tcp.local.",
                        "_homekit._tcp.local.",
                        "_hap._tcp.local.",
                    ]

                    discovered_services: list[str] = []

                    # Query each service type
                    # Note: mDNS queries are broadcast-based, so we query
                    # for services and check if they match our target IP
                    for service_type in service_types:
                        try:
                            # Try to get service info by constructing a service name
                            # This is a simplified approach - real mDNS discovery
                            # would use ServiceBrowser to listen for announcements
                            service_name = (
                                f"{device_ip.replace('.', '-')}.{service_type}"
                            )
                            info = await azc.async_get_service_info(
                                service_type,
                                service_name,
                                timeout=int(self.timeout * 1000),
                            )
                            if info:
                                # Check if the service's IP matches our target
                                addresses = info.addresses_by_version(
                                    info.IPVersion.All
                                )
                                if any(addr == device_ip for addr in addresses):
                                    discovered_services.append(service_type)
                                    # Extract hostname from service info
                                    if info.server and not hostname:
                                        hostname = info.server.rstrip(".")
                        except Exception as e:
                            logger.debug(
                                f"mDNS query for {service_type} on {device_ip} "
                                f"failed: {e}"
                            )
                            continue

                    if discovered_services:
                        services = discovered_services
                        fingerprint["mdns_services"] = services

                    if hostname:
                        fingerprint["dhcp_opt12_hostname"] = hostname

            except ImportError:
                # Fallback: raw socket mDNS query (simpler, less reliable)
                logger.debug("zeroconf not available, using raw socket mDNS")
                fingerprint = await self._enrich_with_raw_socket(device_ip)

        except Exception as e:
            logger.warning(f"mDNS enrichment failed for {device_ip}: {e}")

        return fingerprint

    async def _enrich_with_raw_socket(self, device_ip: str) -> dict[str, Any]:
        """
        Fallback mDNS enrichment using raw socket.

        Args:
            device_ip: Device IP address

        Returns:
            Dictionary with fingerprint data
        """
        fingerprint: dict[str, Any] = {}

        try:
            # Create UDP socket for mDNS
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(self.timeout)

            # Send mDNS query for _services._dns-sd._udp.local
            # This is a simplified query - full mDNS requires proper DNS packet
            # construction
            query = b"\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
            query += b"\x09_services\x07_dns-sd\x04_udp\x05local\x00"
            query += b"\x00\x0c\x00\x01"

            try:
                sock.sendto(query, self.mdns_multicast)
                # Wait for response (simplified - real mDNS needs proper
                # parsing)
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.debug(f"Raw socket mDNS query failed: {e}")
            finally:
                sock.close()

        except Exception as e:
            logger.debug(f"Raw socket mDNS enrichment failed: {e}")

        return fingerprint


async def enrich_with_mdns(
    device_ip: str, device_mac: str, timeout: float = 3.0
) -> dict[str, Any]:
    """
    Convenience function for mDNS enrichment.

    Args:
        device_ip: Device IP address
        device_mac: Device MAC address
        timeout: Timeout for mDNS queries

    Returns:
        Dictionary with fingerprint data
    """
    enricher = MDNSEnricher(timeout=timeout)
    return await enricher.enrich_device(device_ip, device_mac)
