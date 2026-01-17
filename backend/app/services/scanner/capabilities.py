"""Scanner capabilities detection for active probing."""

import logging
import os
import sys

logger = logging.getLogger(__name__)


class ScannerCapabilities:
    """Detects available scanning capabilities based on platform and permissions."""

    def __init__(self):
        self.platform = sys.platform
        self.has_root = self._check_root()
        self.has_net_raw = self._check_net_raw()
        self.has_net_admin = self._check_net_admin()

    def _check_root(self) -> bool:
        """Check if running as root."""
        return os.geteuid() == 0 if hasattr(os, "geteuid") else False

    def _check_net_raw(self) -> bool:
        """Check if NET_RAW capability is available."""
        # On Linux, check /proc/sys/kernel/cap_last_cap or try to create raw socket
        if self.platform.startswith("linux"):
            try:
                import socket

                # Try to create a raw socket (requires CAP_NET_RAW)
                sock = socket.socket(
                    socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP
                )
                sock.close()
                return True
            except (OSError, PermissionError):
                return False
        # macOS/Windows may have different permission models
        return self.has_root or False

    def _check_net_admin(self) -> bool:
        """Check if NET_ADMIN capability is available."""
        # NET_ADMIN is mainly for routing/iptables operations
        # For our purposes, we primarily need NET_RAW for ARP/ICMP
        return self.has_root or False

    def can_arp_sweep(self) -> bool:
        """Check if ARP sweep is possible."""
        return self.has_net_raw or self.has_root

    def can_icmp_ping(self) -> bool:
        """Check if ICMP ping is possible."""
        # ICMP ping typically requires root on Linux, but may work on macOS
        if self.platform == "darwin":
            # macOS may allow ICMP without root in some cases
            return True
        return self.has_net_raw or self.has_root

    def can_raw_socket(self) -> bool:
        """Check if raw socket access is available."""
        return self.has_net_raw or self.has_root

    def get_recommended_discovery_method(self) -> str:
        """Get recommended discovery method based on capabilities."""
        if self.can_arp_sweep():
            return "arp_sweep"
        elif self.can_icmp_ping():
            return "icmp_sweep"
        else:
            return "tcp_probe"

    def get_status(self) -> dict:
        """Get capability status dictionary."""
        return {
            "platform": self.platform,
            "has_root": self.has_root,
            "has_net_raw": self.has_net_raw,
            "has_net_admin": self.has_net_admin,
            "can_arp_sweep": self.can_arp_sweep(),
            "can_icmp_ping": self.can_icmp_ping(),
            "recommended_method": self.get_recommended_discovery_method(),
        }


# Global singleton
_capabilities_instance: ScannerCapabilities | None = None


def get_scanner_capabilities() -> ScannerCapabilities:
    """Get global ScannerCapabilities instance."""
    global _capabilities_instance
    if _capabilities_instance is None:
        _capabilities_instance = ScannerCapabilities()
    return _capabilities_instance
