"""SSDP/UPnP enrichment for device fingerprinting (Stage B)."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# SSDP multicast address and port
SSDP_MULTICAST = ("239.255.255.250", 1900)
SSDP_MX = 3  # Maximum wait time in seconds
HTTP_FETCH_SEMAPHORE = asyncio.Semaphore(4)
MAX_XML_BYTES = 4096


def _is_private_ip(ip_str: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj.is_private or ip_obj.is_loopback
    except ValueError:
        return False


class SSDPEnricher:
    """SSDP/UPnP enrichment to gather device description information."""

    def __init__(self, timeout: float = 5.0):
        """
        Initialize SSDP enricher.

        Args:
            timeout: Timeout for SSDP queries in seconds
        """
        self.timeout = timeout

    async def enrich_device(self, device_ip: str, device_mac: str) -> dict[str, Any]:
        """
        Enrich device fingerprint using SSDP queries.

        Args:
            device_ip: Device IP address
            device_mac: Device MAC address

        Returns:
            Dictionary with fingerprint data (ssdp_manufacturer, ssdp_model, etc.)
        """
        fingerprint: dict[str, Any] = {}
        if not _is_private_ip(device_ip):
            return fingerprint

        try:
            # Send SSDP M-SEARCH request and wait for responses
            responses = await self._send_ssdp_search(device_ip)

            if responses:
                # Parse SSDP responses and extract device info
                device_info = await self._parse_ssdp_responses(responses)

                if device_info:
                    if device_info.get("usn"):
                        fingerprint["ssdp_usn"] = device_info["usn"]
                    if device_info.get("st"):
                        fingerprint["ssdp_st"] = device_info["st"]
                    if device_info.get("location"):
                        fingerprint["ssdp_location"] = device_info["location"]
                    if device_info.get("server"):
                        fingerprint["ssdp_server"] = device_info["server"]
                    if device_info.get("device_type"):
                        fingerprint["ssdp_device_type"] = device_info["device_type"]
                    if device_info.get("manufacturer"):
                        fingerprint["ssdp_manufacturer"] = device_info["manufacturer"]
                    if device_info.get("model"):
                        fingerprint["ssdp_model"] = device_info["model"]
                    if device_info.get("model_name"):
                        fingerprint["ssdp_model_name"] = device_info["model_name"]
                    if device_info.get("friendly_name"):
                        fingerprint["ssdp_friendly_name"] = device_info["friendly_name"]

        except Exception as e:
            logger.debug(f"SSDP enrichment failed for {device_ip}: {e}")

        return fingerprint

    async def _send_ssdp_search(self, target_ip: str) -> list[str]:
        """
        Send SSDP M-SEARCH request and collect responses.

        Args:
            target_ip: Target device IP address

        Returns:
            List of SSDP response strings
        """
        responses: list[str] = []

        try:
            # Create UDP socket for SSDP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(self.timeout)

            # SSDP M-SEARCH request
            search_request = (
                "M-SEARCH * HTTP/1.1\r\n"
                f"HOST: {SSDP_MULTICAST[0]}:{SSDP_MULTICAST[1]}\r\n"
                'MAN: "ssdp:discover"\r\n'
                f"MX: {SSDP_MX}\r\n"
                "ST: ssdp:all\r\n"
                "\r\n"
            ).encode()

            # Send multicast M-SEARCH
            try:
                sock.sendto(search_request, SSDP_MULTICAST)

                # Collect responses (non-blocking with timeout)
                end_time = asyncio.get_event_loop().time() + self.timeout

                while asyncio.get_event_loop().time() < end_time:
                    try:
                        sock.settimeout(0.5)  # Short timeout for each recv
                        data, addr = sock.recvfrom(4096)
                        # Filter responses from target IP
                        if addr[0] == target_ip:
                            response = data.decode("utf-8", errors="ignore")
                            responses.append(response)
                    except TimeoutError:
                        # Continue waiting until overall timeout
                        continue
                    except Exception as e:
                        logger.debug(f"Error receiving SSDP response: {e}")
                        break

            except Exception as e:
                logger.debug(f"SSDP M-SEARCH send failed: {e}")
            finally:
                sock.close()

        except Exception as e:
            logger.debug(f"SSDP socket setup failed: {e}")

        return responses

    async def _parse_ssdp_responses(self, responses: list[str]) -> dict[str, Any]:
        """
        Parse SSDP responses and extract device information.

        Args:
            responses: List of SSDP response strings

        Returns:
            Dictionary with parsed device information
        """
        device_info: dict[str, Any] = {}

        for response in responses:
            lines = response.split("\r\n")
            headers: dict[str, str] = {}

            # Parse HTTP headers
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip().lower()] = value.strip()

            # Extract useful headers
            location = headers.get("location")
            server = headers.get("server")
            st = headers.get("st") or headers.get("nt")
            usn = headers.get("usn")

            if location and "ssdp_location" not in device_info:
                device_info["location"] = location
            if server and "server" not in device_info:
                device_info["server"] = server
            if st and "device_type" not in device_info:
                device_info["device_type"] = st
            if st:
                device_info.setdefault("st", st)
            if usn:
                device_info.setdefault("usn", usn)

            # Try to fetch device description XML from location
            if location:
                try:
                    desc_info = await self._fetch_device_description(location)
                    if desc_info:
                        for key, value in desc_info.items():
                            device_info.setdefault(key, value)
                except Exception as e:
                    logger.debug(f"Failed to fetch device description: {e}")

        return device_info

    async def _fetch_device_description(self, url: str) -> dict[str, Any]:
        """
        Fetch and parse UPnP device description XML.

        Args:
            url: URL of the device description XML

        Returns:
            Dictionary with parsed device information
        """
        info: dict[str, Any] = {}

        try:
            parsed = urlparse(url)
            host = parsed.hostname
            if not host or not _is_private_ip(host):
                return info

            async with HTTP_FETCH_SEMAPHORE:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(2.0),
                    follow_redirects=True,
                    verify=False,
                    limits=httpx.Limits(max_connections=4, max_keepalive_connections=4),
                    headers={"User-Agent": "ZenetHunter/ssdp-ident"},
                ) as client:
                    resp = await client.get(url)
                    if resp.status_code >= 400:
                        return info
                    collected = b""
                    async for chunk in resp.aiter_bytes():
                        collected += chunk
                        if len(collected) > MAX_XML_BYTES:
                            collected = collected[:MAX_XML_BYTES]
                            break
                    xml_data = collected.decode("utf-8", errors="ignore")

            # Parse XML using ElementTree for safety
            import xml.etree.ElementTree as ET

            try:
                root = ET.fromstring(xml_data)
            except ET.ParseError:
                return info

            def _find_text(tag: str) -> str | None:
                elem = root.find(f".//{tag}")
                if elem is not None and elem.text:
                    return elem.text.strip()
                return None

            manufacturer = _find_text("manufacturer")
            model_name = _find_text("modelName")
            model_number = _find_text("modelNumber")
            friendly_name = _find_text("friendlyName")
            if manufacturer:
                info["manufacturer"] = manufacturer
            if model_name:
                info["model_name"] = model_name
            if model_number:
                info["model"] = model_number
            if friendly_name:
                info["friendly_name"] = friendly_name

        except Exception as e:
            logger.debug(f"Device description fetch failed for {url}: {e}")

        return info


async def enrich_with_ssdp(
    device_ip: str, device_mac: str, timeout: float = 5.0
) -> dict[str, Any]:
    """
    Convenience function for SSDP enrichment.

    Args:
        device_ip: Device IP address
        device_mac: Device MAC address
        timeout: Timeout for SSDP queries

    Returns:
        Dictionary with fingerprint data
    """
    enricher = SSDPEnricher(timeout=timeout)
    return await enricher.enrich_device(device_ip, device_mac)
