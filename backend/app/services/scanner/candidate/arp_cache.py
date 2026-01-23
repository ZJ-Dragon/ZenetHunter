"""ARP/Neighbor cache reader for candidate device discovery.

Reads local system ARP cache and neighbor tables to generate candidate
device list without active network scanning.
"""

import asyncio
import logging
import re
import subprocess
import sys
from datetime import UTC, datetime
from typing import NamedTuple

logger = logging.getLogger(__name__)


class ARPCandidate(NamedTuple):
    """ARP cache entry representing a potential device."""

    ip: str
    mac: str
    interface: str | None
    last_seen: datetime  # When this entry was last updated in cache
    source: str  # "arp-cache" or "neighbor-cache"


async def get_arp_candidates() -> list[ARPCandidate]:
    """Read system ARP cache to get candidate devices.

    Returns candidate devices from local ARP/neighbor cache without
    sending any network packets.

    Returns:
        List of ARPCandidate entries from system cache

    Note:
        - Linux: uses `ip neigh` or `arp -an`
        - macOS: uses `arp -an`
        - Windows: uses `arp -a`
    """
    platform = sys.platform

    if platform == "darwin":
        return await _read_macos_arp_cache()
    elif platform.startswith("linux"):
        return await _read_linux_neighbor_cache()
    elif platform == "win32":
        return await _read_windows_arp_cache()
    else:
        logger.warning(f"Unsupported platform for ARP cache: {platform}")
        return []


async def _read_macos_arp_cache() -> list[ARPCandidate]:
    """Read ARP cache on macOS using 'arp -an'."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "arp",
            "-an",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)

        if proc.returncode != 0:
            logger.warning(
                f"arp command failed: {stderr.decode('utf-8', errors='ignore')}"
            )
            return []

        output = stdout.decode("utf-8", errors="ignore")
        candidates = []

        # Parse arp output: ? (192.168.1.1) at aa:bb:cc:dd:ee:ff on en0 ifscope [ethernet]
        for line in output.splitlines():
            match = re.search(
                r"\(([0-9.]+)\)\s+at\s+([0-9a-f:]{17})\s+on\s+(\w+)",
                line,
                re.IGNORECASE,
            )
            if match:
                ip, mac, interface = match.groups()
                # Normalize MAC to lowercase
                mac = mac.lower()
                candidates.append(
                    ARPCandidate(
                        ip=ip,
                        mac=mac,
                        interface=interface,
                        last_seen=datetime.now(UTC),  # Approx time
                        source="arp-cache",
                    )
                )

        logger.info(f"Read {len(candidates)} candidates from macOS ARP cache")
        return candidates

    except TimeoutError:
        logger.error("ARP cache read timed out")
        return []
    except Exception as e:
        logger.error(f"Failed to read macOS ARP cache: {e}", exc_info=True)
        return []


async def _read_linux_neighbor_cache() -> list[ARPCandidate]:
    """Read neighbor cache on Linux using 'ip neigh'."""
    try:
        # Try 'ip neigh' first (preferred)
        proc = await asyncio.create_subprocess_exec(
            "ip",
            "neigh",
            "show",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)

        if proc.returncode != 0:
            # Fallback to 'arp -an'
            return await _read_linux_arp_fallback()

        output = stdout.decode("utf-8", errors="ignore")
        candidates = []

        # Parse ip neigh: 192.168.1.1 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE
        for line in output.splitlines():
            match = re.search(
                r"([0-9.]+)\s+dev\s+(\w+)\s+lladdr\s+([0-9a-f:]{17})",
                line,
                re.IGNORECASE,
            )
            if match:
                ip, interface, mac = match.groups()
                mac = mac.lower()
                # Check state (REACHABLE, STALE, DELAY)
                state = "REACHABLE"
                if "STALE" in line:
                    state = "STALE"
                elif "DELAY" in line:
                    state = "DELAY"

                candidates.append(
                    ARPCandidate(
                        ip=ip,
                        mac=mac,
                        interface=interface,
                        last_seen=datetime.now(UTC),
                        source="neighbor-cache",
                    )
                )

        logger.info(f"Read {len(candidates)} candidates from Linux neighbor cache")
        return candidates

    except TimeoutError:
        logger.error("Neighbor cache read timed out")
        return []
    except Exception as e:
        logger.error(f"Failed to read Linux neighbor cache: {e}", exc_info=True)
        return []


async def _read_linux_arp_fallback() -> list[ARPCandidate]:
    """Fallback to 'arp -an' on Linux if 'ip neigh' fails."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "arp",
            "-an",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
        output = stdout.decode("utf-8", errors="ignore")
        candidates = []

        # Parse: ? (192.168.1.1) at aa:bb:cc:dd:ee:ff [ether] on eth0
        for line in output.splitlines():
            match = re.search(
                r"\(([0-9.]+)\)\s+at\s+([0-9a-f:]{17})\s+.*on\s+(\w+)",
                line,
                re.IGNORECASE,
            )
            if match:
                ip, mac, interface = match.groups()
                candidates.append(
                    ARPCandidate(
                        ip=ip,
                        mac=mac.lower(),
                        interface=interface,
                        last_seen=datetime.now(UTC),
                        source="arp-cache",
                    )
                )

        logger.info(
            f"Read {len(candidates)} candidates from Linux ARP cache (fallback)"
        )
        return candidates

    except Exception as e:
        logger.error(f"ARP fallback failed: {e}")
        return []


async def _read_windows_arp_cache() -> list[ARPCandidate]:
    """Read ARP cache on Windows using 'arp -a'."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "arp",
            "-a",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=(
                subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            ),
        )

        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)

        if proc.returncode != 0:
            logger.warning(f"arp failed: {stderr.decode('utf-8', errors='ignore')}")
            return []

        output = stdout.decode("utf-8", errors="ignore")
        candidates = []

        # Parse Windows arp: 192.168.1.1          aa-bb-cc-dd-ee-ff     dynamic
        for line in output.splitlines():
            match = re.search(
                r"([0-9.]+)\s+([0-9a-f-]{17})\s+(dynamic|static)",
                line,
                re.IGNORECASE,
            )
            if match:
                ip, mac, entry_type = match.groups()
                # Convert Windows MAC format (aa-bb-cc-dd-ee-ff) to standard (aa:bb:cc:dd:ee:ff)
                mac = mac.replace("-", ":").lower()
                candidates.append(
                    ARPCandidate(
                        ip=ip,
                        mac=mac,
                        interface=None,  # Windows arp doesn't show interface easily
                        last_seen=datetime.now(UTC),
                        source="arp-cache",
                    )
                )

        logger.info(f"Read {len(candidates)} candidates from Windows ARP cache")
        return candidates

    except TimeoutError:
        logger.error("Windows ARP cache read timed out")
        return []
    except Exception as e:
        logger.error(f"Failed to read Windows ARP cache: {e}", exc_info=True)
        return []
