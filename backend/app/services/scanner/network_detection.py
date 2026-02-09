"""Network subnet detection from ARP cache and system routing.

Detects the local network subnet by:
1. Reading ARP cache to find active devices
2. Detecting default gateway from system routing table
3. Inferring subnet from IP addresses found
"""

import asyncio
import ipaddress
import logging
import re
import subprocess
import sys
from typing import NamedTuple

from app.services.scanner.candidate.arp_cache import get_arp_candidates

logger = logging.getLogger(__name__)


class NetworkInfo(NamedTuple):
    """Detected network information."""

    subnet: str  # CIDR notation, e.g., "192.168.31.0/24"
    gateway_ip: str | None  # Gateway IP address
    interface: str | None  # Primary network interface
    method: str  # Detection method: "arp", "gateway", "fallback"


async def detect_local_subnet() -> NetworkInfo:
    """
    Detect local network subnet using multiple methods.

    Priority:
    1. ARP cache analysis (most reliable)
    2. Default gateway detection
    3. Fallback to config default

    Returns:
        NetworkInfo with detected subnet and metadata
    """
    # Method 1: Analyze ARP cache
    try:
        arp_candidates = await get_arp_candidates()
        if arp_candidates:
            subnet_info = _infer_subnet_from_arp(arp_candidates)
            if subnet_info:
                logger.info(
                    f"Detected subnet from ARP cache: {subnet_info.subnet} "
                    f"(gateway: {subnet_info.gateway_ip})"
                )
                return subnet_info
    except Exception as e:
        logger.warning(f"ARP-based subnet detection failed: {e}")

    # Method 2: Detect from default gateway
    try:
        gateway_info = await _detect_from_gateway()
        if gateway_info:
            logger.info(
                f"Detected subnet from gateway: {gateway_info.subnet} "
                f"(gateway: {gateway_info.gateway_ip})"
            )
            return gateway_info
    except Exception as e:
        logger.warning(f"Gateway-based subnet detection failed: {e}")

    # Method 3: Fallback to config default
    from app.core.config import get_settings

    settings = get_settings()
    fallback_subnet = settings.scan_range
    logger.warning(
        "Could not detect subnet automatically, "
        f"using config default: {fallback_subnet}"
    )
    return NetworkInfo(
        subnet=fallback_subnet,
        gateway_ip=None,
        interface=None,
        method="fallback",
    )


def _infer_subnet_from_arp(
    candidates: list,
) -> NetworkInfo | None:
    """
    Infer subnet from ARP cache entries.

    Strategy:
    1. Group IPs by /24 subnet
    2. Find the subnet with most devices (likely the main LAN)
    3. Identify gateway (usually .1 or .254)

    Args:
        candidates: List of ARPCandidate entries

    Returns:
        NetworkInfo or None if inference fails
    """
    if not candidates:
        return None

    # Extract IPs and group by /24 subnet
    ip_addresses = []
    gateway_candidates = []

    for candidate in candidates:
        try:
            ip = ipaddress.IPv4Address(candidate.ip)
            ip_addresses.append(ip)

            # Common gateway IPs: .1, .254, .0.1
            if ip.packed[-1] in (1, 254) or (ip.packed[-2] == 0 and ip.packed[-1] == 1):
                gateway_candidates.append((ip, candidate.mac))
        except ValueError:
            continue

    if not ip_addresses:
        return None

    # Group by /24 subnet
    subnet_counts: dict[str, int] = {}
    subnet_ips: dict[str, list[ipaddress.IPv4Address]] = {}

    for ip in ip_addresses:
        # Get /24 network
        network = ipaddress.IPv4Network(f"{ip}/24", strict=False)
        subnet_str = str(network)
        subnet_counts[subnet_str] = subnet_counts.get(subnet_str, 0) + 1
        if subnet_str not in subnet_ips:
            subnet_ips[subnet_str] = []
        subnet_ips[subnet_str].append(ip)

    if not subnet_counts:
        return None

    # Find subnet with most devices (likely main LAN)
    main_subnet = max(subnet_counts.items(), key=lambda x: x[1])[0]
    main_ips = subnet_ips[main_subnet]

    # Try to identify gateway
    gateway_ip = None
    network_obj = ipaddress.IPv4Network(main_subnet, strict=False)
    # Common gateway IPs in order of likelihood
    gateway_tests = [
        network_obj.network_address + 1,  # .1
        network_obj.broadcast_address - 1,  # .254
        network_obj.network_address + 256,  # .0.1 (for /16)
    ]

    for test_ip in gateway_tests:
        if test_ip in main_ips:
            gateway_ip = str(test_ip)
            break

    # If no gateway found, check gateway_candidates in main subnet
    if not gateway_ip:
        for gip, _ in gateway_candidates:
            if gip in main_ips:
                gateway_ip = str(gip)
                break

    # Get interface from first candidate (if available)
    interface = None
    for candidate in candidates:
        if candidate.interface:
            interface = candidate.interface
            break

    return NetworkInfo(
        subnet=main_subnet,
        gateway_ip=gateway_ip,
        interface=interface,
        method="arp",
    )


async def _detect_from_gateway() -> NetworkInfo | None:
    """
    Detect subnet from default gateway IP.

    Uses system routing table to find default gateway,
    then infers /24 subnet from gateway IP.

    Returns:
        NetworkInfo or None if detection fails
    """
    platform = sys.platform
    gateway_ip = None
    interface = None

    try:
        if platform == "darwin":
            # macOS: netstat -rn | grep default
            proc = await asyncio.create_subprocess_exec(
                "netstat",
                "-rn",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3.0)
            if proc.returncode == 0:
                output = stdout.decode("utf-8", errors="ignore")
                for line in output.splitlines():
                    if "default" in line.lower():
                        # Format: default 192.168.31.1 UGSc en0 (columns collapsed)
                        match = re.search(r"default\s+([0-9.]+)\s+.*?\s+(\w+)", line)
                        if match:
                            gateway_ip = match.group(1)
                            interface = match.group(2)
                            break

        elif platform.startswith("linux"):
            # Linux: ip route | grep default
            proc = await asyncio.create_subprocess_exec(
                "ip",
                "route",
                "show",
                "default",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3.0)
            if proc.returncode == 0:
                output = stdout.decode("utf-8", errors="ignore")
                # Format: default via 192.168.31.1 dev eth0
                match = re.search(r"via\s+([0-9.]+).*?dev\s+(\w+)", output)
                if match:
                    gateway_ip = match.group(1)
                    interface = match.group(2)

        elif platform == "win32":
            # Windows: route print | findstr "0.0.0.0"
            proc = await asyncio.create_subprocess_exec(
                "route",
                "print",
                "0.0.0.0",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                ),
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3.0)
            if proc.returncode == 0:
                output = stdout.decode("utf-8", errors="ignore")
                # Parse Windows route output
                for line in output.splitlines():
                    match = re.search(r"0\.0\.0\.0\s+0\.0\.0\.0\s+([0-9.]+)", line)
                    if match:
                        gateway_ip = match.group(1)
                        break

        if gateway_ip:
            # Infer /24 subnet from gateway IP
            try:
                gateway = ipaddress.IPv4Address(gateway_ip)
                network = ipaddress.IPv4Network(f"{gateway}/24", strict=False)
                subnet = str(network)

                return NetworkInfo(
                    subnet=subnet,
                    gateway_ip=gateway_ip,
                    interface=interface,
                    method="gateway",
                )
            except ValueError:
                pass

    except Exception as e:
        logger.debug(f"Gateway detection error: {e}")

    return None
