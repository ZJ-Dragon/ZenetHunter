"""Capability detection for active network scanning."""

import logging
import os
import sys
from typing import NamedTuple

logger = logging.getLogger(__name__)


class ScanCapabilities(NamedTuple):
    """Network scanning capabilities available on the current platform."""

    can_arp_sweep: bool
    can_icmp_ping: bool
    can_tcp_probe: bool
    can_mdns: bool
    can_ssdp: bool
    can_nbns: bool
    can_snmp: bool
    is_root: bool
    platform: str
    reason: str | None = None


def detect_scan_capabilities() -> ScanCapabilities:
    """
    Detect available network scanning capabilities on current platform.

    Returns:
        ScanCapabilities with detected capabilities and reason if limited
    """
    platform = sys.platform
    is_root = os.geteuid() == 0 if hasattr(os, "geteuid") else False
    can_arp_sweep = False
    can_icmp_ping = False
    can_tcp_probe = False
    can_mdns = False
    can_ssdp = False
    can_nbns = False
    can_snmp = False
    reason = None

    # ARP Sweep: requires root or NET_RAW capability on Linux
    if platform.startswith("linux"):
        can_arp_sweep = is_root or _has_capability("NET_RAW")
        if not can_arp_sweep:
            reason = "ARP sweep requires root or NET_RAW capability"
    elif platform == "darwin":
        # macOS may allow ARP operations without root in some cases
        can_arp_sweep = True  # Try and fall back if needed
    elif platform == "win32":
        # Windows: raw sockets may require admin
        can_arp_sweep = _is_windows_admin()
    else:
        reason = f"Unsupported platform for ARP sweep: {platform}"

    # ICMP Ping: generally requires root or NET_RAW on Linux
    if platform.startswith("linux"):
        can_icmp_ping = is_root or _has_capability("NET_RAW")
    elif platform in ("darwin", "win32"):
        # macOS/Windows: ping may work without root in some cases
        can_icmp_ping = True
    else:
        can_icmp_ping = False

    # TCP Probe: generally available (connect-based, no special permissions)
    can_tcp_probe = True

    # mDNS: available if socket support exists
    can_mdns = True  # Can try, fall back on error

    # SSDP: UDP multicast, generally available
    can_ssdp = True

    # NBNS: Windows-specific, but can be probed
    if platform == "win32":
        can_nbns = True
    else:
        can_nbns = False  # NBNS is Windows-specific

    # SNMP: requires library and credentials (not auto-detected as "capable")
    can_snmp = False  # Only if library installed and configured

    logger.info(
        f"Scan capabilities detected: platform={platform}, "
        f"root={is_root}, arp_sweep={can_arp_sweep}, "
        f"icmp_ping={can_icmp_ping}, tcp_probe={can_tcp_probe}"
    )

    return ScanCapabilities(
        can_arp_sweep=can_arp_sweep,
        can_icmp_ping=can_icmp_ping,
        can_tcp_probe=can_tcp_probe,
        can_mdns=can_mdns,
        can_ssdp=can_ssdp,
        can_nbns=can_nbns,
        can_snmp=can_snmp,
        is_root=is_root,
        platform=platform,
        reason=reason,
    )


def _has_capability(cap_name: str) -> bool:
    """Check if process has a Linux capability."""
    try:
        import prctl

        if cap_name == "NET_RAW":
            return prctl.cap_effective.net_raw
        return False
    except (ImportError, AttributeError):
        # prctl not available or capability not present
        return False


def _is_windows_admin() -> bool:
    """Check if running as Windows administrator."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False
