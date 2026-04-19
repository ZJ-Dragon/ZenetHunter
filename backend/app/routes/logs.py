import sys
from collections.abc import Iterable
from datetime import UTC, datetime
import json
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.capabilities import get_capability_reporting_service
from app.core.config import get_settings
from app.core.database import get_db
from app.infrastructure.runtime_checks import collect_runtime_diagnostics
from app.models.log import SystemLog
from app.repositories.event_log import EventLogRepository
from app.services.state import StateManager, get_state_manager

router = APIRouter(prefix="/logs", tags=["logs"])


def _normalize_timestamp(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _log_identity(log: SystemLog) -> tuple[str, str, str, str, str | None, str]:
    context_key = json.dumps(log.context or {}, sort_keys=True, default=str)
    return (
        _normalize_timestamp(log.timestamp).isoformat(),
        log.level.lower(),
        log.module,
        log.message,
        log.device_mac,
        context_key,
    )


def _merge_logs(*log_sets: Iterable[SystemLog], limit: int) -> list[SystemLog]:
    merged: list[SystemLog] = []
    seen: set[tuple[str, str, str, str, str | None, str]] = set()

    combined = sorted(
        (log for logs in log_sets for log in logs),
        key=lambda item: _normalize_timestamp(item.timestamp),
        reverse=True,
    )
    for log in combined:
        identity = _log_identity(log)
        if identity in seen:
            continue
        seen.add(identity)
        merged.append(log)
        if len(merged) >= limit:
            break

    return merged


@router.get("", response_model=list[SystemLog])
async def get_logs(
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    state: StateManager = Depends(get_state_manager),
    db: AsyncSession = Depends(get_db),
):
    """Get recent system logs from both runtime state and persisted audit storage."""
    repo = EventLogRepository(db)
    persisted_logs = await repo.get_logs(limit=limit)
    runtime_logs = state.get_logs(limit=limit)
    return _merge_logs(persisted_logs, runtime_logs, limit=limit)


@router.post("", response_model=None, status_code=201)
async def add_log(
    log: SystemLog,
    state: StateManager = Depends(get_state_manager),
    db: AsyncSession = Depends(get_db),
):
    """Add a system log entry."""
    repo = EventLogRepository(db)
    await repo.add_log(
        level=log.level,
        module=log.module,
        message=log.message,
        correlation_id=log.correlation_id,
        device_mac=log.device_mac,
        context=log.context,
    )
    state.add_log(log)


@router.get("/system-info")
async def get_system_info() -> dict[str, Any]:
    """Get system information for debugging."""
    from app.core.platform.detect import get_platform_features

    settings = get_settings()
    platform_features = get_platform_features()
    summary = platform_features.get_summary()
    capability_report = get_capability_reporting_service().get_serialized_report()
    runtime = collect_runtime_diagnostics().to_dict()

    return {
        "platform": summary["platform"],
        "platform_name": summary["platform_name"],
        "platform_version": summary["platform_version"],
        "python_version": sys.version.split()[0],
        "app_version": settings.app_version,
        "app_env": settings.app_env,
        "database_url": "***" if settings.database_url else None,  # Hide sensitive info
        "docker": summary["is_docker"],
        "capabilities": summary["capabilities"],
        "capability_state": capability_report["capabilities"],
        "runtime": runtime,
    }
