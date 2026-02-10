"""SSDP/UPnP enrichment for device fingerprinting (Stage B)."""

import asyncio
import logging
import socket
from typing import Any

logger = logging.getLogger(__name__)

# SSDP multicast address and port
SSDP_MULTICAST = ("239.255.255.250", 1900)
SSDP_MX = 3  # Maximum wait time in seconds


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

        try:
            # Send SSDP M-SEARCH request and wait for responses
            responses = await self._send_ssdp_search(device_ip)

            if responses:
                # Parse SSDP responses and extract device info
                device_info = self._parse_ssdp_responses(responses)

                if device_info:
                    # Extract manufacturer/model from device info
                    if device_info.get("manufacturer"):
                        fingerprint["ssdp_manufacturer"] = device_info["manufacturer"]
                    if device_info.get("model"):
                        fingerprint["ssdp_model"] = device_info["model"]
                    if device_info.get("model_name"):
                        fingerprint["ssdp_model_name"] = device_info["model_name"]
                    if device_info.get("device_type"):
                        fingerprint["ssdp_device_type"] = device_info["device_type"]
                    if device_info.get("server"):
                        fingerprint["ssdp_server"] = device_info["server"]
                    if device_info.get("location"):
                        fingerprint["ssdp_location"] = device_info["location"]

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

    def _parse_ssdp_responses(self, responses: list[str]) -> dict[str, Any]:
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
            if "location" in headers:
                device_info["location"] = headers["location"]

            if "server" in headers:
                device_info["server"] = headers["server"]

            if "st" in headers or "nt" in headers:
                device_type = headers.get("st") or headers.get("nt")
                if device_type:
                    device_info["device_type"] = device_type

            # Try to fetch device description XML from location
            if "location" in headers:
                try:
                    desc_info = self._fetch_device_description(headers["location"])
                    if desc_info:
                        device_info.update(desc_info)
                except Exception as e:
                    logger.debug(f"Failed to fetch device description: {e}")

        return device_info

    def _fetch_device_description(self, url: str) -> dict[str, Any]:
        """
        Fetch and parse UPnP device description XML.

        Args:
            url: URL of the device description XML

        Returns:
            Dictionary with parsed device information
        """
        info: dict[str, Any] = {}

        try:
            import urllib.request

            # Fetch XML with timeout
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3) as response:
                xml_data = response.read().decode("utf-8", errors="ignore")

                # Simple XML parsing (extract manufacturer/model)
                # Note: Full XML parsing would use xml.etree.ElementTree
                # but we use simple regex for minimal dependencies
                import re

                # Extract manufacturer
                manufacturer_match = re.search(
                    r"<manufacturer[^>]*>(.*?)</manufacturer>",
                    xml_data,
                    re.IGNORECASE | re.DOTALL,
                )
                if manufacturer_match:
                    info["manufacturer"] = manufacturer_match.group(1).strip()

                # Extract model name
                model_name_match = re.search(
                    r"<modelName[^>]*>(.*?)</modelName>",
                    xml_data,
                    re.IGNORECASE | re.DOTALL,
                )
                if model_name_match:
                    info["model_name"] = model_name_match.group(1).strip()

                # Extract model number
                model_match = re.search(
                    r"<modelNumber[^>]*>(.*?)</modelNumber>",
                    xml_data,
                    re.IGNORECASE | re.DOTALL,
                )
                if model_match:
                    info["model"] = model_match.group(1).strip()

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
