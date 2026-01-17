"""Active ARP sweep for device discovery (Stage A)."""

import asyncio
import ipaddress
import logging
import socket

logger = logging.getLogger(__name__)


class ARPSweep:
    """Active ARP sweep using raw sockets or Scapy."""

    def __init__(self, timeout: float = 2.0, concurrency: int = 50):
        """
        Initialize ARP sweep.

        Args:
            timeout: Timeout per probe in seconds
            concurrency: Max concurrent probes
        """
        self.timeout = timeout
        self.concurrency = concurrency

    async def sweep_subnet(
        self, subnet: str, interface: str | None = None
    ) -> list[tuple[str, str | None, str]]:
        """
        Perform active ARP sweep on a subnet.

        Args:
            subnet: CIDR subnet to scan (e.g., "192.168.1.0/24")
            interface: Network interface to use (None = auto-detect)

        Returns:
            List of (IP, MAC, interface) tuples. MAC may be None if not discovered.
        """
        try:
            network = ipaddress.ip_network(subnet, strict=False)
        except ValueError as e:
            logger.error(f"Invalid subnet {subnet}: {e}")
            return []

        # Generate IP targets (exclude network/broadcast)
        ip_targets = [str(ip) for ip in network.hosts()]

        logger.info(
            f"Starting ARP sweep: subnet={subnet}, "
            f"targets={len(ip_targets)}, timeout={self.timeout}s, "
            f"concurrency={self.concurrency}"
        )

        # Try Scapy first (preferred if available)
        try:
            from scapy.all import ARP, Ether, get_if_addr, get_if_hwaddr, srp

            results = await self._sweep_with_scapy(ip_targets, interface)
            return results
        except ImportError:
            logger.debug("Scapy not available, trying raw socket")
        except Exception as e:
            logger.warning(f"Scapy ARP sweep failed: {e}, falling back to raw socket")

        # Fallback: raw socket (Linux/macOS with root)
        try:
            results = await self._sweep_with_raw_socket(ip_targets, interface)
            return results
        except Exception as e:
            logger.error(f"Raw socket ARP sweep failed: {e}", exc_info=True)
            return []

    async def _sweep_with_scapy(
        self, ip_targets: list[str], interface: str | None
    ) -> list[tuple[str, str | None, str]]:
        """
        Perform ARP sweep using Scapy.

        Args:
            ip_targets: List of IP addresses to probe
            interface: Network interface to use

        Returns:
            List of (IP, MAC, interface) tuples
        """
        from scapy.all import ARP, Ether, srp

        # Get interface and MAC
        if interface is None:
            # Auto-detect: use default interface
            try:
                interface = socket.gethostbyname(socket.gethostname())
            except Exception:
                interface = None

        results: list[tuple[str, str | None, str]] = []

        # Send ARP requests in batches with concurrency control
        semaphore = asyncio.Semaphore(self.concurrency)

        async def probe_ip(ip: str) -> tuple[str, str | None, str] | None:
            async with semaphore:
                try:
                    # Use asyncio to run Scapy's synchronous srp
                    loop = asyncio.get_event_loop()
                    arp_req = ARP(pdst=ip)
                    # Run Scapy in executor (it's synchronous)
                    answered, _unanswered = await loop.run_in_executor(
                        None,
                        lambda: srp(
                            Ether(dst="ff:ff:ff:ff:ff:ff") / arp_req,
                            timeout=self.timeout,
                            verbose=0,
                            iface=interface,
                        ),
                    )

                    if answered:
                        for _sent, received in answered:
                            mac = received.hwsrc
                            return (ip, mac, interface or "unknown")
                    return None
                except Exception as e:
                    logger.debug(f"ARP probe failed for {ip}: {e}")
                    return None

        # Run probes concurrently
        tasks = [probe_ip(ip) for ip in ip_targets]
        probe_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect valid results
        for result in probe_results:
            if result and isinstance(result, tuple):
                results.append(result)

        logger.info(f"ARP sweep completed: found {len(results)} devices")
        return results

    async def _sweep_with_raw_socket(
        self, ip_targets: list[str], interface: str | None
    ) -> list[tuple[str, str | None, str]]:
        """
        Perform ARP sweep using raw socket (fallback).

        Args:
            ip_targets: List of IP addresses to probe
            interface: Network interface to use

        Returns:
            List of (IP, MAC, interface) tuples

        Note: Raw socket requires root/CAP_NET_RAW on Linux.
        """
        # Raw socket implementation is platform-specific and complex
        # For now, return empty list (can be implemented later if needed)
        logger.warning("Raw socket ARP sweep not yet implemented")
        return []


async def arp_sweep(
    subnet: str,
    timeout: float = 2.0,
    concurrency: int = 50,
    interface: str | None = None,
) -> list[tuple[str, str | None, str]]:
    """
    Convenience function for ARP sweep.

    Args:
        subnet: CIDR subnet to scan
        timeout: Timeout per probe in seconds
        concurrency: Max concurrent probes
        interface: Network interface to use

    Returns:
        List of (IP, MAC, interface) tuples
    """
    sweeper = ARPSweep(timeout=timeout, concurrency=concurrency)
    return await sweeper.sweep_subnet(subnet, interface)
