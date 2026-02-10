"""Repository for probe observations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.probe_observation import ProbeObservationModel


class ProbeObservationRepository:
    """Data access for probe observations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        *,
        device_mac: str,
        scan_run_id: str | None,
        protocol: str,
        key_fields: dict,
        keywords: list[str],
        keyword_hits: list[dict],
        raw_summary: str | None,
        redaction_level: str = "standard",
        timestamp: datetime | None = None,
    ) -> ProbeObservationModel:
        record = ProbeObservationModel(
            device_mac=device_mac.lower(),
            scan_run_id=scan_run_id,
            protocol=protocol,
            timestamp=timestamp or datetime.now(UTC),
            key_fields=key_fields,
            keywords=keywords,
            keyword_hits=keyword_hits,
            raw_summary=raw_summary,
            redaction_level=redaction_level,
        )
        self.session.add(record)
        return record

    async def list_by_device(
        self,
        device_mac: str,
        *,
        limit: int = 50,
        since: datetime | None = None,
    ) -> list[ProbeObservationModel]:
        stmt = (
            select(ProbeObservationModel)
            .where(ProbeObservationModel.device_mac == device_mac.lower())
            .order_by(ProbeObservationModel.timestamp.desc())
            .limit(limit)
        )
        if since:
            stmt = stmt.where(ProbeObservationModel.timestamp >= since)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_scan(self, scan_run_id: str) -> list[ProbeObservationModel]:
        stmt = (
            select(ProbeObservationModel)
            .where(ProbeObservationModel.scan_run_id == str(scan_run_id))
            .order_by(ProbeObservationModel.timestamp.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def to_ndjson(records: Iterable[ProbeObservationModel]) -> str:
        """Serialize observations to NDJSON."""
        import json

        lines: list[str] = []
        for rec in records:
            payload = {
                "id": rec.id,
                "device_mac": rec.device_mac,
                "scan_run_id": rec.scan_run_id,
                "protocol": rec.protocol,
                "timestamp": rec.timestamp.isoformat(),
                "key_fields": rec.key_fields,
                "keywords": rec.keywords,
                "keyword_hits": rec.keyword_hits,
                "raw_summary": rec.raw_summary,
                "redaction_level": rec.redaction_level,
            }
            lines.append(json.dumps(payload, ensure_ascii=False))
        return "\n".join(lines)
