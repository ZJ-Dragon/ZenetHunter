import sys
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.application.capabilities import get_capability_reporting_service
from app.core.config import get_settings
from app.infrastructure.runtime_checks import collect_runtime_diagnostics
from app.models.log import SystemLog
from app.services.state import StateManager, get_state_manager

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=list[SystemLog])
async def get_logs(
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    state: StateManager = Depends(get_state_manager),
):
    """Get recent system logs."""
    return state.get_logs(limit=limit)


@router.post("", response_model=None, status_code=201)
async def add_log(log: SystemLog, state: StateManager = Depends(get_state_manager)):
    """Add a system log entry."""
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
