"""Active probing enrichment: query devices directly to get their information.

This module implements various active probing techniques to "ask" devices
directly for their name, model, and other identifying information by
simulating normal server connections.
"""

import asyncio
import logging
import re
import socket
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class ActiveProbeEnricher:
    """Active probe enricher that queries devices directly."""

    def __init__(self, timeout: float = 3.0):
        """
        Initialize active probe enricher.

        Args:
            timeout: Timeout for each probe in seconds
        """
        self.timeout = timeout

    async def enrich_device(self, device_ip: str, device_mac: str) -> dict[str, Any]:
        """
        Enrich device by actively querying it.

        Tries multiple methods:
        1. HTTP/HTTPS requests to common ports
        2. Telnet/SSH banner grabbing
        3. SNMP queries (if enabled)
        4. Protocol-specific queries (printer, IoT, etc.)

        Args:
            device_ip: Device IP address
            device_mac: Device MAC address

        Returns:
            Dictionary with fingerprint data
        """
        fingerprint: dict[str, Any] = {}

        # Run all probes concurrently
        tasks = [
            self._probe_http(device_ip),
            self._probe_telnet_banner(device_ip),
            self._probe_ssh_banner(device_ip),
            self._probe_printer_protocol(device_ip),
            self._probe_iot_protocols(device_ip),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge results
        for result in results:
            if isinstance(result, dict):
                fingerprint.update(result)
            elif isinstance(result, Exception):
                logger.debug(f"Probe failed: {result}")

        return fingerprint

    async def _probe_http(self, device_ip: str) -> dict[str, Any]:
        """
        Probe device via HTTP/HTTPS on common ports.

        Tries to:
        1. GET / on common ports (80, 8080, 443, 8443)
        2. Extract device info from HTTP headers (Server, X-Powered-By, etc.)
        3. Parse HTML title/device info from response

        Args:
            device_ip: Device IP address

        Returns:
            Dictionary with HTTP fingerprint data
        """
        fingerprint: dict[str, Any] = {}
        common_ports = [80, 8080, 443, 8443, 8000, 8888]

        async with httpx.AsyncClient(
            timeout=self.timeout, follow_redirects=True, verify=False
        ) as client:
            # Use verify=False to accept self-signed certs for IoT devices
            for port in common_ports:
                try:
                    # Try HTTP/HTTPS
                    if port in [443, 8443]:
                        url = f"https://{device_ip}:{port}"
                    else:
                        url = f"http://{device_ip}:{port}"

                    try:
                        response = await client.get(url, timeout=self.timeout)

                        # Extract HTTP headers
                        server = response.headers.get("Server", "")
                        if server:
                            fingerprint["http_server"] = server

                        powered_by = response.headers.get("X-Powered-By", "")
                        if powered_by:
                            fingerprint["http_powered_by"] = powered_by

                        # Try to extract device info from HTML
                        if "text/html" in response.headers.get("Content-Type", ""):
                            html = response.text[:5000]  # First 5KB
                            device_info = self._parse_html_for_device_info(html)
                            if device_info:
                                fingerprint.update(device_info)

                        # If we got a response, record the port
                        fingerprint["http_port"] = port
                        fingerprint["http_status"] = response.status_code

                        logger.debug(
                            f"HTTP probe {device_ip}:{port} - "
                            f"Server: {server}, Status: {response.status_code}"
                        )
                        break  # Found working port, no need to try others

                    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError):
                        continue  # Try next port
                    except Exception as e:
                        logger.debug(f"HTTP probe {device_ip}:{port} failed: {e}")
                        continue

                except Exception as e:
                    logger.debug(f"HTTP probe setup for {device_ip}:{port} failed: {e}")
                    continue

        return fingerprint

    def _parse_html_for_device_info(self, html: str) -> dict[str, Any]:
        """
        Parse HTML to extract device information.

        Looks for:
        - <title> tags
        - Device name/model in meta tags
        - Common device identifiers in HTML comments

        Args:
            html: HTML content

        Returns:
            Dictionary with parsed device info
        """
        info: dict[str, Any] = {}

        # Extract title
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()
            # Clean up title (remove extra whitespace)
            title = re.sub(r"\s+", " ", title)
            if title and len(title) < 200:  # Reasonable title length
                info["http_title"] = title

        # Extract meta tags
        meta_patterns = {
            "device": r'<meta[^>]*name=["\']device["\'][^>]*content=["\']([^"\']+)["\']',
            "model": r'<meta[^>]*name=["\']model["\'][^>]*content=["\']([^"\']+)["\']',
            "product": r'<meta[^>]*name=["\']product["\'][^>]*content=["\']([^"\']+)["\']',
        }

        for key, pattern in meta_patterns.items():
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                info[f"http_meta_{key}"] = match.group(1).strip()

        # Look for common device identifiers in HTML comments
        comment_patterns = [
            r"<!--\s*Device:\s*([^>]+)\s*-->",
            r"<!--\s*Model:\s*([^>]+)\s*-->",
            r"<!--\s*Product:\s*([^>]+)\s*-->",
        ]

        for pattern in comment_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if "device" not in info:
                    info["http_device_comment"] = value
                break

        return info

    async def _probe_telnet_banner(self, device_ip: str) -> dict[str, Any]:
        """
        Probe device via Telnet banner grabbing.

        Connects to common Telnet ports and reads the banner message,
        which often contains device name/model.

        Args:
            device_ip: Device IP address

        Returns:
            Dictionary with Telnet banner data
        """
        fingerprint: dict[str, Any] = {}
        telnet_ports = [23, 2323]

        for port in telnet_ports:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(device_ip, port),
                    timeout=self.timeout,
                )

                # Read banner (first 512 bytes)
                try:
                    banner = await asyncio.wait_for(reader.read(512), timeout=1.0)
                    banner_text = banner.decode("utf-8", errors="ignore").strip()

                    if banner_text:
                        # Clean up banner
                        banner_text = re.sub(r"\x1b\[[0-9;]*m", "", banner_text)  # Remove ANSI codes
                        banner_text = re.sub(r"\s+", " ", banner_text)  # Normalize whitespace

                        if len(banner_text) > 5 and len(banner_text) < 200:
                            fingerprint["telnet_banner"] = banner_text
                            logger.debug(f"Telnet banner from {device_ip}:{port}: {banner_text[:50]}")

                except asyncio.TimeoutError:
                    pass

                writer.close()
                await writer.wait_closed()

                if "telnet_banner" in fingerprint:
                    break  # Found banner, no need to try other ports

            except (ConnectionRefusedError, asyncio.TimeoutError, OSError):
                continue
            except Exception as e:
                logger.debug(f"Telnet probe {device_ip}:{port} failed: {e}")
                continue

        return fingerprint

    async def _probe_ssh_banner(self, device_ip: str) -> dict[str, Any]:
        """
        Probe device via SSH banner grabbing.

        Connects to SSH port and reads the SSH banner, which often
        contains device/OS information.

        Args:
            device_ip: Device IP address

        Returns:
            Dictionary with SSH banner data
        """
        fingerprint: dict[str, Any] = {}

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(device_ip, 22),
                timeout=self.timeout,
            )

            # Read SSH banner (first line)
            try:
                banner = await asyncio.wait_for(reader.readline(), timeout=1.0)
                banner_text = banner.decode("utf-8", errors="ignore").strip()

                if banner_text:
                    # SSH banner format: SSH-2.0-OpenSSH_7.9 or SSH-2.0-Cisco-1.25
                    fingerprint["ssh_banner"] = banner_text
                    logger.debug(f"SSH banner from {device_ip}: {banner_text}")

                    # Try to extract device info from banner
                    # Example: "SSH-2.0-Cisco-1.25" -> "Cisco"
                    if "Cisco" in banner_text:
                        fingerprint["ssh_vendor"] = "Cisco"
                    elif "OpenSSH" in banner_text:
                        # Could be Linux/Unix device
                        fingerprint["ssh_type"] = "OpenSSH"

            except asyncio.TimeoutError:
                pass

            writer.close()
            await writer.wait_closed()

        except (ConnectionRefusedError, asyncio.TimeoutError, OSError):
            pass
        except Exception as e:
            logger.debug(f"SSH probe {device_ip} failed: {e}")

        return fingerprint

    async def _probe_printer_protocol(self, device_ip: str) -> dict[str, Any]:
        """
        Probe device via printer protocols (IPP, LPD, etc.).

        Many printers expose device information via IPP (Internet Printing Protocol)
        or LPD (Line Printer Daemon).

        Args:
            device_ip: Device IP address

        Returns:
            Dictionary with printer protocol data
        """
        fingerprint: dict[str, Any] = {}

        # Try IPP (Internet Printing Protocol) on port 631
        try:
            # IPP request to get printer attributes
            ipp_request = (
                b"\x02\x00"  # Version 2.0
                b"\x00\x0a"  # Get-Printer-Attributes operation
                b"\x00\x00\x00\x01"  # Request ID
                b"\x01"  # Operation attributes tag
                b"\x47"  # charset tag
                b"\x00\x12attributes-charset\x00\x05utf-8"
                b"\x48"  # natural language tag
                b"\x00\x1battributes-natural-language\x00\x02en"
                b"\x45"  # URI tag
                b"\x00\x0bprinter-uri\x00\x1ahttp://" + device_ip.encode() + b":631/"
                b"\x03"  # End of attributes
            )

            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(device_ip, 631),
                timeout=self.timeout,
            )

            writer.write(ipp_request)
            await writer.drain()

            try:
                response = await asyncio.wait_for(reader.read(4096), timeout=1.0)
                # Parse IPP response (simplified - full parsing would use proper IPP library)
                response_str = response.decode("utf-8", errors="ignore")
                if "printer" in response_str.lower() or "ipp" in response_str.lower():
                    fingerprint["printer_protocol"] = "IPP"
                    logger.debug(f"IPP response from {device_ip}")
            except asyncio.TimeoutError:
                pass

            writer.close()
            await writer.wait_closed()

        except (ConnectionRefusedError, asyncio.TimeoutError, OSError):
            pass
        except Exception as e:
            logger.debug(f"IPP probe {device_ip} failed: {e}")

        # Try LPD (Line Printer Daemon) on port 515
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(device_ip, 515),
                timeout=self.timeout,
            )

            # LPD: Send \x02 (receive job) command
            writer.write(b"\x02")
            await writer.drain()

            try:
                response = await asyncio.wait_for(reader.read(256), timeout=1.0)
                if response:
                    fingerprint["printer_protocol"] = "LPD"
                    logger.debug(f"LPD response from {device_ip}")
            except asyncio.TimeoutError:
                pass

            writer.close()
            await writer.wait_closed()

        except (ConnectionRefusedError, asyncio.TimeoutError, OSError):
            pass
        except Exception as e:
            logger.debug(f"LPD probe {device_ip} failed: {e}")

        return fingerprint

    async def _probe_iot_protocols(self, device_ip: str) -> dict[str, Any]:
        """
        Probe device via IoT-specific protocols.

        Tries common IoT device protocols:
        - CoAP (Constrained Application Protocol) on port 5683
        - MQTT (if broker on device)
        - Custom IoT protocols

        Args:
            device_ip: Device IP address

        Returns:
            Dictionary with IoT protocol data
        """
        fingerprint: dict[str, Any] = {}

        # Try CoAP (port 5683)
        try:
            # CoAP GET request to /.well-known/core
            coap_request = bytes([
                0x40, 0x01, 0x00, 0x00,  # Header: Ver=1, T=CON, Code=GET, MID=0
                0xb7, 0x2a,  # Token
                0x00, 0x01,  # Option: Uri-Path: ".well-known"
                0x00, 0x04,  # Option: Uri-Path: "core"
            ])

            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(device_ip, 5683),
                timeout=self.timeout,
            )

            writer.write(coap_request)
            await writer.drain()

            try:
                response = await asyncio.wait_for(reader.read(512), timeout=1.0)
                if response:
                    fingerprint["iot_protocol"] = "CoAP"
                    logger.debug(f"CoAP response from {device_ip}")
            except asyncio.TimeoutError:
                pass

            writer.close()
            await writer.wait_closed()

        except (ConnectionRefusedError, asyncio.TimeoutError, OSError):
            pass
        except Exception as e:
            logger.debug(f"CoAP probe {device_ip} failed: {e}")

        return fingerprint


async def enrich_with_active_probe(
    device_ip: str, device_mac: str, timeout: float = 3.0
) -> dict[str, Any]:
    """
    Convenience function for active probe enrichment.

    Args:
        device_ip: Device IP address
        device_mac: Device MAC address
        timeout: Timeout for each probe

    Returns:
        Dictionary with fingerprint data
    """
    enricher = ActiveProbeEnricher(timeout=timeout)
    return await enricher.enrich_device(device_ip, device_mac)
