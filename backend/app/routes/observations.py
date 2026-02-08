"""Observation retrieval endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, ErrorCode
from app.core.security import get_current_user
from app.models.auth import User
from app.models.observation import ProbeObservation, ProbeObservationList
from app.repositories.probe_observation import ProbeObservationRepository
from app.core.database import get_db

router = APIRouter(tags=["observations"])


def _parse_since(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:  # pragma: no cover - defensive
        raise AppError(
            ErrorCode.API_BAD_REQUEST,
            "Invalid 'since' parameter, expected ISO 8601 timestamp",
        ) from exc


@router.get(
    "/devices/{mac}/observations",
    response_model=ProbeObservationList,
    summary="List observations for a device",
)
async def list_device_observations(
    mac: str = Path(..., pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"),
    limit: int = Query(50, ge=1, le=200),
    since: str | None = Query(None, description="ISO timestamp filter"),
    format: str = Query("json", pattern="^(json|ndjson)$"),
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: AsyncSession = Depends(get_db),
):
    repo = ProbeObservationRepository(db)
    records = await repo.list_by_device(mac, limit=limit, since=_parse_since(since))

    if format == "ndjson":
        ndjson = repo.to_ndjson(records)
        return PlainTextResponse(
            ndjson,
            media_type="application/x-ndjson",
            headers={"X-Observation-Count": str(len(records))},
        )

    items = [ProbeObservation.model_validate(rec) for rec in records]
    return ProbeObservationList(items=items, total=len(items))


@router.get(
    "/scan/{scan_run_id}/observations",
    response_model=ProbeObservationList,
    summary="List observations for a scan run",
)
async def list_scan_observations(
    scan_run_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: AsyncSession = Depends(get_db),
    format: str = Query("json", pattern="^(json|ndjson)$"),
):
    repo = ProbeObservationRepository(db)
    records = await repo.list_by_scan(scan_run_id)
    if format == "ndjson":
        ndjson = repo.to_ndjson(records)
        return PlainTextResponse(
            ndjson,
            media_type="application/x-ndjson",
            headers={"X-Observation-Count": str(len(records))},
        )
    items = [ProbeObservation.model_validate(rec) for rec in records]
    return ProbeObservationList(items=items, total=len(items))
