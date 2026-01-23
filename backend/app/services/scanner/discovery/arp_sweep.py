"""Active ARP sweep for device discovery (Stage A)."""

import asyncio
import ipaddress
import logging

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
            # Check if Scapy is available (imports are done in _sweep_with_scapy)
            import scapy.all  # noqa: F401

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
        from scapy.all import ARP, Ether, conf, get_if_list, srp

        # Get interface name (Scapy needs interface name, not IP address)
        if interface is None:
            # Auto-detect: use Scapy's default interface
            try:
                # Use Scapy's conf.iface for default interface
                interface = conf.iface if hasattr(conf, "iface") else None
                # If conf.iface is not set, try to get first available interface
                if not interface:
                    if_list = get_if_list()
                    if if_list:
                        # Prefer en0, en1, etc. on macOS, or eth0, wlan0 on Linux
                        for iface in if_list:
                            if iface.startswith(("en", "eth", "wlan")):
                                interface = iface
                                break
                        # If no preferred interface found, use first one
                        if not interface:
                            interface = if_list[0]
                logger.debug(
                    f"Auto-detected interface: {interface} "
                    f"(available: {get_if_list()})"
                )
            except Exception as e:
                logger.warning(f"Failed to auto-detect interface: {e}")
                interface = None

        logger.info(
            f"Starting ARP sweep with Scapy: {len(ip_targets)} targets, "
            f"interface={interface}, timeout={self.timeout}s"
        )

        results: list[tuple[str, str | None, str]] = []

        # ⚡ OPTIMIZED: Use Scapy's batch scanning instead of per-IP srp
        # This is MUCH faster: single srp call for entire subnet vs 254 calls
        
        try:
            # Create ARP request for all targets at once
            # Join IPs with "/" for Scapy's multi-target format
            # Or use CIDR directly if available
            
            # For better performance, scan in chunks
            CHUNK_SIZE = 50  # Scan 50 IPs at a time
            
            for chunk_start in range(0, len(ip_targets), CHUNK_SIZE):
                chunk = ip_targets[chunk_start:chunk_start + CHUNK_SIZE]
                chunk_num = chunk_start // CHUNK_SIZE + 1
                total_chunks = (len(ip_targets) + CHUNK_SIZE - 1) // CHUNK_SIZE
                
                logger.info(
                    f"Scanning chunk {chunk_num}/{total_chunks} "
                    f"({len(chunk)} IPs)..."
                )
                
                # Build packet list for this chunk
                packets = [
                    Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip) 
                    for ip in chunk
                ]
                
                try:
                    # Run batch srp in executor (single call for whole chunk)
                    loop = asyncio.get_event_loop()
                    answered, _unanswered = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: srp(
                                packets,
                                timeout=self.timeout,
                                verbose=0,
                                iface=interface,
                            ),
                        ),
                        timeout=self.timeout + 5.0,  # Add 5s buffer
                    )
                    
                    # Collect results from this chunk
                    for _sent, received in answered:
                        ip = received.psrc
                        mac = received.hwsrc
                        results.append((ip, mac, interface or "unknown"))
                    
                    logger.debug(
                        f"Chunk {chunk_num} complete: "
                        f"found {len(answered)} devices"
                    )
                    
                except asyncio.TimeoutError:
                    logger.warning(
                        f"Chunk {chunk_num} timed out, continuing..."
                    )
                except Exception as e:
                    logger.warning(
                        f"Chunk {chunk_num} failed: {e}, continuing..."
                    )
                
                # Brief pause between chunks to avoid network flooding
                if chunk_start + CHUNK_SIZE < len(ip_targets):
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"ARP sweep failed: {e}", exc_info=True)

        logger.info(
            f"ARP sweep completed: found {len(results)} devices "
            f"from {len(ip_targets)} targets"
        )
        
        if len(results) == 0:
            logger.warning(
                f"ARP sweep found no devices. "
                f"Check interface={interface}, subnet range, and permissions."
            )
        
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
