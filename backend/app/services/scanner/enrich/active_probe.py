"""Active probing enrichment: safe local-only HTTP and printer identification."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import re
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

HTTP_PORTS = [80, 8080, 443, 8443, 8000, 8888]
HTTP_SEMAPHORE = asyncio.Semaphore(6)
READ_LIMIT = 4096


def _is_private_ip(ip_str: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj.is_private or ip_obj.is_loopback
    except ValueError:
        return False


@dataclass
class ActiveProbeResult:
    fingerprint: dict[str, Any]
    observations: list[dict[str, Any]]


class ActiveProbeEnricher:
    """Active probe enricher that queries devices directly (local-only)."""

    def __init__(
        self,
        timeout: float = 3.0,
        response_limit: int = READ_LIMIT,
        *,
        feature_http: bool = True,
        feature_printer: bool = True,
    ):
        """
        Initialize active probe enricher.

        Args:
            timeout: Timeout for each probe in seconds
            response_limit: Max bytes to read from responses
            feature_http: Enable HTTP/HTTPS identification
            feature_printer: Enable printer identification when hints exist
        """
        self.timeout = timeout
        self.response_limit = response_limit
        self.feature_http = feature_http
        self.feature_printer = feature_printer

    async def enrich_device(
        self,
        device_ip: str,
        device_mac: str,
        *,
        mdns_data: dict[str, Any] | None = None,
        ssdp_data: dict[str, Any] | None = None,
    ) -> ActiveProbeResult | None:
        """Run safe probes against a confirmed-online, local device."""
        if not _is_private_ip(device_ip):
            return None

        fingerprint: dict[str, Any] = {}
        observations: list[dict[str, Any]] = []
        tasks = []

        if self.feature_http:
            tasks.append(self._probe_http(device_ip))
        if self.feature_printer and self._has_printer_hint(mdns_data, ssdp_data):
            tasks.append(self._probe_printer_protocol(device_ip))

        # Lightweight banners for extra hints
        tasks.append(self._probe_telnet_banner(device_ip))
        tasks.append(self._probe_ssh_banner(device_ip))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, ActiveProbeResult):
                fingerprint.update(result.fingerprint)
                observations.extend(result.observations)
            elif isinstance(result, dict):
                fingerprint.update(result)
            elif isinstance(result, Exception):
                logger.debug("Probe failed for %s: %s", device_ip, result)

        return ActiveProbeResult(fingerprint=fingerprint, observations=observations)

    @staticmethod
    def _has_printer_hint(
        mdns_data: dict[str, Any] | None, ssdp_data: dict[str, Any] | None
    ) -> bool:
        mdns_services = mdns_data.get("mdns_services") if mdns_data else []
        mdns_instances = mdns_data.get("mdns_instances") if mdns_data else []
        ssdp_type = (ssdp_data or {}).get("ssdp_device_type") or ""
        ssdp_server = (ssdp_data or {}).get("ssdp_server") or ""
        hints = [ssdp_type.lower(), ssdp_server.lower()]

        for svc in mdns_services or []:
            svc_lower = str(svc).lower()
            if "ipp" in svc_lower or "printer" in svc_lower or "print" in svc_lower:
                return True
        for inst in mdns_instances or []:
            svc_type = str(inst.get("type", "")).lower()
            if "ipp" in svc_type or "printer" in svc_type or "print" in svc_type:
                return True
        return any("printer" in h or "ipp" in h for h in hints)

    async def _probe_http(self, device_ip: str) -> ActiveProbeResult:
        fingerprint: dict[str, Any] = {}
        observations: list[dict[str, Any]] = []

        for port in HTTP_PORTS:
            url = f"http://{device_ip}:{port}"
            if port in (443, 8443):
                url = f"https://{device_ip}:{port}"
            try:
                async with HTTP_SEMAPHORE:
                    async with httpx.AsyncClient(
                        timeout=httpx.Timeout(self.timeout),
                        follow_redirects=True,
                        verify=False,
                        limits=httpx.Limits(
                            max_connections=6, max_keepalive_connections=6
                        ),
                        headers={"User-Agent": "ZenetHunter/http-ident"},
                    ) as client:
                        response = await client.get(url)
                server = response.headers.get("Server")
                status = response.status_code
                body_text = await self._read_limited_body(response)
                html_info = self._parse_html_for_device_info(body_text)

                http_fields: dict[str, Any] = {
                    "http_status": status,
                    "http_port": port,
                }
                if server:
                    http_fields["http_server"] = server

                fingerprint.update(http_fields)
                fingerprint.update(html_info)

                obs_fields = {
                    k: v
                    for k, v in {**http_fields, **html_info}.items()
                    if v is not None
                }
                observations.append(
                    {
                        "protocol": "http_ident",
                        "key_fields": obs_fields,
                        "summary": f"http {status} {server or ''}".strip(),
                    }
                )
                break  # success, skip other ports
            except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPError):
                continue
            except Exception as exc:
                logger.debug("HTTP probe failed for %s:%s: %s", device_ip, port, exc)
                continue

        return ActiveProbeResult(fingerprint=fingerprint, observations=observations)

    async def _read_limited_body(self, response: httpx.Response) -> str:
        """Read a capped amount of body text to avoid large payloads."""
        collected = b""
        async for chunk in response.aiter_bytes():
            collected += chunk
            if len(collected) >= self.response_limit:
                collected = collected[: self.response_limit]
                break
        return collected.decode("utf-8", errors="ignore")

    def _parse_html_for_device_info(self, html: str) -> dict[str, Any]:
        """
        Parse HTML to extract device information.

        Looks for:
        - <title> tags
        - Device name/model in meta tags
        - Common device identifiers in HTML comments
        """
        info: dict[str, Any] = {}

        # Extract title
        title_match = re.search(
            r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
        )
        if title_match:
            title = title_match.group(1).strip()
            title = re.sub(r"\s+", " ", title)
            if title and len(title) < 200:
                info["http_title"] = title

        # Extract meta tags
        meta_patterns = {
            "device": (
                r'<meta[^>]*name=["\']device["\'][^>]*content=["\']([^"\']+)["\']'
            ),
            "model": r'<meta[^>]*name=["\']model["\'][^>]*content=["\']([^"\']+)["\']',
            "product": (
                r'<meta[^>]*name=["\']product["\'][^>]*content=["\']([^"\']+)["\']'
            ),
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

    async def _probe_telnet_banner(self, device_ip: str) -> ActiveProbeResult:
        fingerprint: dict[str, Any] = {}
        observations: list[dict[str, Any]] = []
        telnet_ports = [23, 2323]

        for port in telnet_ports:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(device_ip, port),
                    timeout=self.timeout,
                )
                try:
                    banner = await asyncio.wait_for(reader.read(256), timeout=1.0)
                    banner_text = banner.decode("utf-8", errors="ignore").strip()
                    if banner_text:
                        cleaned = re.sub(r"\s+", " ", banner_text)
                        fingerprint["telnet_banner"] = cleaned[:200]
                        observations = [
                            {
                                "protocol": "telnet_banner",
                                "key_fields": {"telnet_banner": cleaned[:160]},
                            }
                        ]
                        break
                finally:
                    writer.close()
                    await writer.wait_closed()
            except (TimeoutError, ConnectionRefusedError, OSError):
                continue
            except Exception as exc:
                logger.debug("Telnet probe %s:%s failed: %s", device_ip, port, exc)
                continue

        return ActiveProbeResult(
            fingerprint=fingerprint, observations=observations or []
        )

    async def _probe_ssh_banner(self, device_ip: str) -> ActiveProbeResult:
        fingerprint: dict[str, Any] = {}
        observations: list[dict[str, Any]] = []

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(device_ip, 22),
                timeout=self.timeout,
            )

            try:
                banner = await asyncio.wait_for(reader.readline(), timeout=1.0)
                banner_text = banner.decode("utf-8", errors="ignore").strip()

                if banner_text:
                    fingerprint["ssh_banner"] = banner_text[:200]
                    if "Cisco" in banner_text:
                        fingerprint["ssh_vendor"] = "Cisco"
                    elif "OpenSSH" in banner_text:
                        fingerprint["ssh_type"] = "OpenSSH"
                    observations.append(
                        {
                            "protocol": "ssh_banner",
                            "key_fields": {"ssh_banner": banner_text[:160]},
                        }
                    )

            finally:
                writer.close()
                await writer.wait_closed()

        except (TimeoutError, ConnectionRefusedError, OSError):
            pass
        except Exception as e:
            logger.debug("SSH probe %s failed: %s", device_ip, e)

        return ActiveProbeResult(fingerprint=fingerprint, observations=observations)

    async def _probe_printer_protocol(self, device_ip: str) -> ActiveProbeResult:
        fingerprint: dict[str, Any] = {}
        observations: list[dict[str, Any]] = []

        # Try IPP (Internet Printing Protocol) on port 631
        try:
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
                response = await asyncio.wait_for(reader.read(512), timeout=1.0)
                response_text = response.decode("utf-8", errors="ignore").lower()
                if "printer" in response_text or "ipp" in response_text:
                    fingerprint["printer_protocol"] = "IPP"
                    observations.append(
                        {
                            "protocol": "printer_ident",
                            "key_fields": {"printer_protocol": "IPP"},
                        }
                    )
            finally:
                writer.close()
                await writer.wait_closed()

        except (TimeoutError, ConnectionRefusedError, OSError):
            pass
        except Exception as e:
            logger.debug("IPP probe %s failed: %s", device_ip, e)

        # Try LPD (Line Printer Daemon) on port 515
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(device_ip, 515),
                timeout=self.timeout,
            )

            writer.write(b"\x02")
            await writer.drain()

            try:
                response = await asyncio.wait_for(reader.read(256), timeout=1.0)
                if response:
                    fingerprint["printer_protocol"] = fingerprint.get(
                        "printer_protocol", "LPD"
                    )
                    observations.append(
                        {
                            "protocol": "printer_ident",
                            "key_fields": {"printer_protocol": "LPD"},
                        }
                    )
            finally:
                writer.close()
                await writer.wait_closed()

        except (TimeoutError, ConnectionRefusedError, OSError):
            pass
        except Exception as e:
            logger.debug("LPD probe %s failed: %s", device_ip, e)

        return ActiveProbeResult(fingerprint=fingerprint, observations=observations)


async def enrich_with_active_probe(
    device_ip: str,
    device_mac: str,
    timeout: float = 3.0,
    *,
    mdns_data: dict[str, Any] | None = None,
    ssdp_data: dict[str, Any] | None = None,
    feature_http: bool = True,
    feature_printer: bool = True,
) -> ActiveProbeResult | None:
    """
    Convenience function for active probe enrichment.

    Args:
        device_ip: Device IP address
        device_mac: Device MAC address
        timeout: Timeout for each probe
        mdns_data: mDNS results for hinting (printer detection)
        ssdp_data: SSDP results for hinting (printer detection)
        feature_http: Enable HTTP identification probe
        feature_printer: Enable printer probe (requires hints)

    Returns:
        ActiveProbeResult with fingerprint data and observations, or None if skipped
    """
    enricher = ActiveProbeEnricher(
        timeout=timeout,
        feature_http=feature_http,
        feature_printer=feature_printer,
    )
    return await enricher.enrich_device(
        device_ip=device_ip,
        device_mac=device_mac,
        mdns_data=mdns_data,
        ssdp_data=ssdp_data,
    )
