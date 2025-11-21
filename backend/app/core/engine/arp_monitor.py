"""Passive ARP Monitoring Engine."""

import asyncio
import logging

logger = logging.getLogger(__name__)


class ArpMonitor:
    """
    Passive engine that listens for ARP packets to detect spoofing.
    Compare source MAC in ARP header vs Ethernet header,
    or track changes in IP-MAC mappings.
    """

    def __init__(self):
        self._is_running = False
        self._known_mappings: dict[str, str] = {}  # IP -> MAC

    async def start_monitoring(self, interface: str = "eth0") -> None:
        """Start the ARP monitoring task."""
        if self._is_running:
            return

        logger.info(f"[ArpMonitor] Starting passive detection on {interface}")
        self._is_running = True
        # In a real implementation, we would spawn a scapy async sniffer here.
        # For MVP/Dummy, we simulate detection.
        asyncio.create_task(self._dummy_monitor_loop())

    async def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self._is_running = False
        logger.info("[ArpMonitor] Stopped.")

    async def _dummy_monitor_loop(self) -> None:
        """Simulate ARP event detection."""
        while self._is_running:
            await asyncio.sleep(10)
            # Simulate a check
            pass

    def detect_spoof(self, ip: str, claimed_mac: str) -> bool:
        """
        Check if an IP-MAC pair contradicts known history.
        Returns True if spoofing is suspected.
        """
        if ip not in self._known_mappings:
            self._known_mappings[ip] = claimed_mac
            return False

        known_mac = self._known_mappings[ip]
        if known_mac != claimed_mac:
            logger.warning(
                f"[ArpMonitor] SPOOF DETECTED! "
                f"IP {ip} moved from {known_mac} to {claimed_mac}"
            )
            return True

        return False
