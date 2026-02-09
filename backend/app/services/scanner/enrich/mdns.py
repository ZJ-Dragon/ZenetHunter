"""mDNS/DNS-SD enrichment for device fingerprinting (Stage B)."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _is_private_ip(ip_str: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj.is_private or ip_obj.is_loopback
    except ValueError:
        return False


def _clean_service_type(service_type: str) -> str:
    """Normalize service type for keyword extraction."""
    cleaned = service_type.strip(".")
    cleaned = cleaned.replace("_tcp", "tcp").replace("_udp", "udp")
    cleaned = cleaned.replace("_", ".")
    return cleaned


class _AsyncMDNSListener:
    """Collect services for a specific device IP."""

    def __init__(self, azc, target_ip: str, timeout_ms: int):
        self.azc = azc
        self.target_ip = target_ip
        self.timeout_ms = timeout_ms
        self.services: list[dict[str, Any]] = []
        self._tasks: set[asyncio.Task[Any]] = set()

    def _create_task(self, coro):
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def add_service(
        self, zeroconf, service_type: str, name: str
    ) -> None:  # pragma: no cover - callback
        self._create_task(self._process_service(service_type, name))

    update_service = add_service
    remove_service = lambda *args, **kwargs: None  # noqa: E731

    async def _process_service(self, service_type: str, name: str) -> None:
        try:
            info = await self.azc.async_get_service_info(
                service_type, name, timeout=self.timeout_ms
            )
            if not info:
                return
            addresses = set(info.parsed_addresses())
            if self.target_ip not in addresses:
                return
            props: dict[str, str] = {}
            for key, value in (info.properties or {}).items():
                try:
                    k = key.decode("utf-8", errors="ignore")
                    v = value.decode("utf-8", errors="ignore")
                    props[k] = v
                except Exception:
                    continue
            service_entry = {
                "type": _clean_service_type(service_type),
                "name": name.rstrip("."),
                "port": info.port,
                "properties": props,
            }
            if info.server:
                service_entry["hostname"] = info.server.rstrip(".")
            self.services.append(service_entry)
        except Exception as exc:
            logger.debug("mDNS service processing failed for %s: %s", name, exc)

    async def wait(self) -> None:
        if not self._tasks:
            return
        await asyncio.gather(*self._tasks, return_exceptions=True)


class MDNSEnricher:
    """mDNS/DNS-SD enrichment to gather device service information."""

    def __init__(self, timeout: float = 3.0):
        """
        Initialize mDNS enricher.

        Args:
            timeout: Timeout for mDNS queries in seconds
        """
        self.timeout = timeout

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
        if not _is_private_ip(device_ip):
            return fingerprint

        try:
            from zeroconf.asyncio import AsyncServiceBrowser, AsyncZeroconf
        except ImportError:
            logger.debug("zeroconf not available; skipping mDNS enrichment")
            return fingerprint

        try:
            async with AsyncZeroconf() as azc:
                listener = _AsyncMDNSListener(
                    azc, target_ip=device_ip, timeout_ms=int(self.timeout * 1000)
                )
                browser = AsyncServiceBrowser(
                    azc.zeroconf,
                    "_services._dns-sd._udp.local.",
                    listener,
                )
                try:
                    await asyncio.sleep(self.timeout)
                finally:
                    try:
                        await browser.async_cancel()
                    except AttributeError:
                        browser.cancel()
                await listener.wait()

            if listener.services:
                fingerprint["mdns_instances"] = listener.services
                fingerprint["mdns_services"] = sorted(
                    {svc.get("type") for svc in listener.services if svc.get("type")}
                )
                hostnames = [
                    svc.get("hostname")
                    for svc in listener.services
                    if svc.get("hostname")
                ]
                if hostnames:
                    fingerprint["mdns_hostname"] = hostnames[0]
                    fingerprint["dhcp_opt12_hostname"] = hostnames[0]

        except Exception as e:
            logger.debug("mDNS enrichment failed for %s: %s", device_ip, e)

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
