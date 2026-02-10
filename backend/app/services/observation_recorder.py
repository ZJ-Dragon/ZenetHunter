"""Observation recording and normalization utilities."""

from __future__ import annotations

import html
import logging
from datetime import datetime
from typing import Any

from app.core.database import get_session_factory
from app.repositories.probe_observation import ProbeObservationRepository
from app.services.keyword_extractor import KeywordExtractor

logger = logging.getLogger(__name__)

# Allowed keys to persist from probe fingerprints
SAFE_FIELD_WHITELIST = {
    "http_title",
    "http_server",
    "http_meta_model",
    "http_meta_device",
    "ssdp_manufacturer",
    "ssdp_model",
    "ssdp_model_name",
    "telnet_banner",
    "ssh_banner",
    "mdns_services",
    "mdns_hostname",
}


def _sanitize_text(value: str, limit: int = 160) -> str:
    """Trim and escape potentially untrusted strings."""
    cleaned = html.escape(value.strip().replace("\r", " ").replace("\n", " "))
    return cleaned[:limit]


def build_key_fields(protocol: str, raw_fields: dict[str, Any]) -> dict[str, Any]:
    """Extract safe key fields from raw probe data."""
    key_fields: dict[str, Any] = {}
    for key, value in raw_fields.items():
        if key not in SAFE_FIELD_WHITELIST:
            continue
        if isinstance(value, str):
            key_fields[key] = _sanitize_text(value)
        elif isinstance(value, list):
            # Keep small lists (e.g., mdns services) with sanitized strings
            sanitized_list = []
            for item in value[:20]:
                if isinstance(item, str):
                    sanitized_list.append(_sanitize_text(item, 80))
                elif isinstance(item, dict) and "name" in item:
                    sanitized_list.append(_sanitize_text(str(item["name"]), 80))
            if sanitized_list:
                key_fields[key] = sanitized_list
        elif isinstance(value, dict):
            # Shallow sanitize dict of strings
            sanitized_dict = {}
            for sub_k, sub_v in list(value.items())[:10]:
                if isinstance(sub_v, str):
                    sanitized_dict[sub_k] = _sanitize_text(sub_v, 80)
            if sanitized_dict:
                key_fields[key] = sanitized_dict
    # Attach protocol tag for context
    if key_fields:
        key_fields["protocol"] = protocol
    return key_fields


def build_summary(protocol: str, key_fields: dict[str, Any]) -> str:
    """Create a short summary from key fields."""
    parts: list[str] = [protocol]
    title = key_fields.get("http_title") or key_fields.get("ssdp_model_name")
    server = key_fields.get("http_server")
    manufacturer = key_fields.get("ssdp_manufacturer")
    if title:
        parts.append(str(title))
    if server and server not in parts:
        parts.append(str(server))
    if manufacturer and manufacturer not in parts:
        parts.append(str(manufacturer))
    return " | ".join(parts)[:200]


class ObservationRecorder:
    """Helper to persist sanitized observations."""

    def __init__(self):
        self.session_factory = get_session_factory()
        self.keyword_extractor = KeywordExtractor()

    async def record(
        self,
        *,
        device_mac: str,
        scan_run_id: str | None,
        protocol: str,
        raw_fields: dict[str, Any],
        timestamp: datetime | None = None,
        redaction_level: str = "standard",
    ) -> None:
        try:
            key_fields = build_key_fields(protocol, raw_fields)
            if not key_fields:
                return
            keywords = self.keyword_extractor.extract(key_fields)
            keyword_hits = self.keyword_extractor.match_rules(keywords, key_fields)
            summary = build_summary(protocol, key_fields)
            async with self.session_factory() as session:
                repo = ProbeObservationRepository(session)
                await repo.add(
                    device_mac=device_mac,
                    scan_run_id=scan_run_id,
                    protocol=protocol,
                    key_fields=key_fields,
                    keywords=keywords,
                    keyword_hits=keyword_hits,
                    raw_summary=summary,
                    redaction_level=redaction_level,
                    timestamp=timestamp,
                )
                await session.commit()
        except Exception as err:  # pragma: no cover - defensive
            logger.warning("Failed to record observation for %s: %s", device_mac, err)
