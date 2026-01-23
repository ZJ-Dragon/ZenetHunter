"""DHCP lease reader for candidate device discovery.

Reads DHCP lease files from common locations to extract device information
without active network scanning.
"""

import asyncio
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

logger = logging.getLogger(__name__)


class DHCPCandidate(NamedTuple):
    """DHCP lease entry representing a potential device."""

    ip: str
    mac: str
    hostname: str | None
    lease_end: datetime | None
    source: str  # "dhcp-lease"


# Common DHCP lease file locations by platform/software
DHCP_LEASE_PATHS = [
    # Linux - ISC DHCP Server
    "/var/lib/dhcp/dhcpd.leases",
    "/var/lib/dhcpd/dhcpd.leases",
    # Linux - dnsmasq
    "/var/lib/misc/dnsmasq.leases",
    "/var/lib/dnsmasq/dnsmasq.leases",
    # macOS - built-in DHCP
    "/var/db/dhcpd_leases",
    # Custom locations (can be added via config)
]


async def get_dhcp_candidates() -> list[DHCPCandidate]:
    """Read DHCP lease files to get candidate devices.

    Attempts to read DHCP lease information from common locations.
    This is a best-effort approach and may not work on all systems.

    Returns:
        List of DHCPCandidate entries from lease files
    """
    candidates = []

    for lease_path in DHCP_LEASE_PATHS:
        path = Path(lease_path)
        if path.exists() and path.is_file():
            try:
                logger.debug(f"Attempting to read DHCP leases from {lease_path}")
                lease_candidates = await _read_lease_file(path)
                if lease_candidates:
                    candidates.extend(lease_candidates)
                    logger.info(
                        f"Read {len(lease_candidates)} candidates from {lease_path}"
                    )
            except Exception as e:
                logger.debug(f"Failed to read {lease_path}: {e}")

    # Remove duplicates (same MAC)
    unique_candidates = {}
    for candidate in candidates:
        # Keep the one with latest lease_end
        if candidate.mac not in unique_candidates:
            unique_candidates[candidate.mac] = candidate
        else:
            existing = unique_candidates[candidate.mac]
            if (
                candidate.lease_end
                and existing.lease_end
                and candidate.lease_end > existing.lease_end
            ):
                unique_candidates[candidate.mac] = candidate

    result = list(unique_candidates.values())
    logger.info(f"Total DHCP candidates: {len(result)} (after dedup)")
    return result


async def _read_lease_file(path: Path) -> list[DHCPCandidate]:
    """Read a DHCP lease file and parse entries.

    Args:
        path: Path to lease file

    Returns:
        List of DHCPCandidate entries
    """
    # Detect format based on content
    try:
        content = await asyncio.to_thread(path.read_text, encoding="utf-8")
    except UnicodeDecodeError:
        # Try binary/different encoding
        content = await asyncio.to_thread(path.read_text, encoding="latin-1")

    # Try different parsers
    if "lease {" in content:
        # ISC DHCP format
        return _parse_isc_dhcp(content)
    elif " " in content and len(content.splitlines()[0].split()) >= 3:
        # dnsmasq format (space-separated)
        return _parse_dnsmasq(content)
    else:
        logger.debug(f"Unknown DHCP lease format in {path}")
        return []


def _parse_isc_dhcp(content: str) -> list[DHCPCandidate]:
    """Parse ISC DHCP Server lease file format.

    Format:
    lease 192.168.1.100 {
      starts 4 2026/01/23 12:00:00;
      ends 4 2026/01/23 18:00:00;
      hardware ethernet aa:bb:cc:dd:ee:ff;
      client-hostname "device-name";
    }
    """
    candidates = []
    lease_pattern = re.compile(
        r"lease\s+([0-9.]+)\s*\{([^}]+)\}", re.MULTILINE | re.DOTALL
    )

    for match in lease_pattern.finditer(content):
        ip = match.group(1)
        lease_body = match.group(2)

        # Extract MAC
        mac_match = re.search(r"hardware ethernet\s+([0-9a-f:]{17})", lease_body, re.I)
        if not mac_match:
            continue
        mac = mac_match.group(1).lower()

        # Extract hostname (optional)
        hostname = None
        hostname_match = re.search(r'client-hostname\s+"([^"]+)"', lease_body)
        if hostname_match:
            hostname = hostname_match.group(1)

        # Extract lease end time (optional)
        lease_end = None
        ends_match = re.search(
            r"ends\s+\d+\s+(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})", lease_body
        )
        if ends_match:
            try:
                lease_end = datetime.strptime(
                    ends_match.group(1), "%Y/%m/%d %H:%M:%S"
                ).replace(tzinfo=UTC)
            except Exception:
                pass

        candidates.append(
            DHCPCandidate(
                ip=ip,
                mac=mac,
                hostname=hostname,
                lease_end=lease_end,
                source="dhcp-lease",
            )
        )

    return candidates


def _parse_dnsmasq(content: str) -> list[DHCPCandidate]:
    """Parse dnsmasq lease file format.

    Format:
    1674480000 aa:bb:cc:dd:ee:ff 192.168.1.100 device-name *
    (timestamp mac ip hostname client-id)
    """
    candidates = []

    for line in content.splitlines():
        parts = line.strip().split()
        if len(parts) < 3:
            continue

        try:
            # timestamp mac ip [hostname] [client-id]
            timestamp = int(parts[0])
            mac = parts[1].lower()
            ip = parts[2]
            hostname = parts[3] if len(parts) > 3 and parts[3] != "*" else None

            # Convert timestamp to datetime
            lease_end = datetime.fromtimestamp(timestamp, tz=UTC)

            # Check if lease is still valid (not expired)
            if lease_end < datetime.now(UTC):
                continue  # Skip expired leases

            candidates.append(
                DHCPCandidate(
                    ip=ip,
                    mac=mac,
                    hostname=hostname,
                    lease_end=lease_end,
                    source="dhcp-lease",
                )
            )
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to parse dnsmasq line '{line}': {e}")
            continue

    return candidates
