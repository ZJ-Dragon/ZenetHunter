"""ARP sweep discovery module for active device probing."""

import asyncio
import ipaddress
import logging
import sys
from typing import Any

from app.core.config import get_settings
from app.services.scanner.capabilities import get_scanner_capabilities

logger = logging.getLogger(__name__)


class ARPSweep:
    """Active ARP sweep for device discovery."""

    def __init__(self):
        self.capabilities = get_scanner_capabilities()
        self.settings = get_settings()

    async def sweep_subnet(
        self, subnet: str, timeout: float | None = None, concurrency: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Perform ARP sweep on a subnet.

        Args:
            subnet: CIDR subnet (e.g., "192.168.1.0/24")
            timeout: Timeout per probe in seconds
            concurrency: Max concurrent probes

        Returns:
            List of discovered devices: [{"ip": str, "mac": str, "interface": str}, ...]
        """
        if timeout is None:
            timeout = self.settings.scan_timeout_sec
        if concurrency is None:
            concurrency = self.settings.scan_concurrency

        if not self.capabilities.can_arp_sweep():
            logger.warning(
                "ARP sweep requires root/NET_RAW capability. "
                "Falling back to non-privileged method."
            )
            return []

        logger.info(
            f"Starting ARP sweep: subnet={subnet}, "
            f"timeout={timeout}s, concurrency={concurrency}"
        )

        try:
            # Try Scapy-based ARP sweep first
            return await self._scapy_arp_sweep(subnet, timeout, concurrency)
        except ImportError:
            logger.warning("Scapy not available, ARP sweep unavailable")
            return []
        except Exception as e:
            logger.error(f"ARP sweep failed: {e}", exc_info=True)
            return []

    async def _scapy_arp_sweep(
        self, subnet: str, timeout: float, concurrency: int
    ) -> list[dict[str, Any]]:
        """Perform ARP sweep using Scapy."""
        try:
            from scapy.all import ARP, Ether, conf, get_if_hwaddr, sendp, srp
        except ImportError as e:
            logger.error(f"Scapy import failed: {e}")
            raise ImportError("Scapy is required for ARP sweep") from e

        # Parse subnet
        network = ipaddress.ip_network(subnet, strict=False)
        target_ips = [str(ip) for ip in network.hosts()]

        logger.debug(f"ARP sweeping {len(target_ips)} IPs in {subnet}")

        # Get interface for sending (prefer non-loopback)
        interface = self._get_default_interface()

        # Create ARP request packets
        packets = []
        for ip in target_ips:
            # Create Ethernet + ARP request
            # dst="ff:ff:ff:ff:ff:ff" is broadcast
            arp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
            packets.append((arp_request, ip))

        # Send ARP requests with concurrency control and timeout
        discovered: list[dict[str, Any]] = []

        # Use semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)

        async def probe_arp(packet_info: tuple[Any, str]) -> dict[str, Any] | None:
            packet, target_ip = packet_info
            async with semaphore:
                try:
                    # Run Scapy srp in executor (it's blocking)
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: srp(
                                packet,
                                timeout=timeout,
                                verbose=0,
                                iface=interface,
                            ),
                        ),
                        timeout=timeout + 1.0,
                    )

                    answered, _ = result
                    if answered:
                        for sent, received in answered:
                            mac = received[Ether].src
                            logger.debug(
                                f"ARP response: {target_ip} -> {mac} "
                                f"(interface: {interface})"
                            )
                            return {
                                "ip": target_ip,
                                "mac": mac.upper(),
                                "interface": interface or "unknown",
                            }
                except TimeoutError:
                    logger.debug(f"ARP probe timeout for {target_ip}")
                except Exception as e:
                    logger.debug(f"ARP probe failed for {target_ip}: {e}")
                return None

        # Execute probes with limited concurrency
        tasks = [probe_arp(pkt_info) for pkt_info in packets]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        for result in results:
            if isinstance(result, dict):
                discovered.append(result)
            elif isinstance(result, Exception):
                logger.debug(f"ARP probe exception: {result}")

        logger.info(f"ARP sweep completed: discovered {len(discovered)} devices")
        return discovered

    def _get_default_interface(self) -> str | None:
        """Get default network interface for ARP sweep."""
        try:
            from scapy.all import conf

            # Get default interface from Scapy config
            if conf.iface:
                return conf.iface

            # Platform-specific fallback
            if sys.platform == "darwin":
                # macOS: try to get primary interface
                import subprocess

                result = subprocess.run(
                    ["route", "get", "default"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                for line in result.stdout.splitlines():
                    if "interface:" in line:
                        return line.split(":")[-1].strip()
            elif sys.platform.startswith("linux"):
                # Linux: try common interfaces
                for iface in ["eth0", "enp0s3", "wlan0", "wlp2s0"]:
                    try:
                        import socket

                        socket.if_nametoindex(iface)
                        return iface
                    except (OSError, AttributeError):
                        continue
        except Exception as e:
            logger.debug(f"Could not determine default interface: {e}")

        return None


# Global singleton
_arp_sweep_instance: ARPSweep | None = None


def get_arp_sweep() -> ARPSweep:
    """Get global ARPSweep instance."""
    global _arp_sweep_instance
    if _arp_sweep_instance is None:
        _arp_sweep_instance = ARPSweep()
    return _arp_sweep_instance
