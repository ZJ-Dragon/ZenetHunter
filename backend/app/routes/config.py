from fastapi import APIRouter, Body, Depends, status

from app.core.security import get_current_admin
from app.models.auth import User
from app.models.setup import (
    AcknowledgeRequest,
    RegisterAdminRequest,
    RegisterAdminResponse,
    SetupStatus,
)
from app.services.reset import ResetService
from app.services.setup import SetupService
from app.services.state import StateManager, get_state_manager

router = APIRouter(prefix="/config", tags=["config"])
setup_service = SetupService()
reset_service = ResetService()


@router.get("/status", response_model=SetupStatus)
async def get_config_status():
    """Check if admin exists and whether first-run is completed."""
    status_flags = await setup_service.get_status()
    return {
        "admin_exists": status_flags["admin_exists"],
        "first_run_completed": status_flags["first_run_completed"],
    }


@router.get("/platform")
async def get_platform_config():
    """
    Get platform configuration information.
    Returns detected platform and available features.
    """
    from app.core.platform.detect import get_platform_features

    platform_features = get_platform_features()
    summary = platform_features.get_summary()

    return {
        "platform": summary["platform"],
        "platform_name": summary["platform_name"],
        "capabilities": summary["capabilities"],
        "recommended_platform": (
            "darwin" if summary["platform"] == "darwin" else summary["platform"]
        ),
    }


@router.get("/scan")
async def get_scan_config():
    """
    Get scan configuration settings.
    Returns current scan settings and feature flags.
    Note: Configuration is read from environment variables,
    this endpoint is read-only for display purposes.

    The scan_range shown is the detected/active subnet, not just the config default.
    """
    from app.core.config import get_settings
    from app.services.scanner.network_detection import detect_local_subnet

    settings = get_settings()

    # Detect actual subnet (will fallback to config if detection fails)
    try:
        network_info = await detect_local_subnet()
        active_scan_range = network_info.subnet
        detection_method = network_info.method
    except Exception as e:
        # If detection fails, use config default
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Subnet detection failed, using config default: {e}")
        active_scan_range = settings.scan_range
        detection_method = "config"

    return {
        "scan_range": active_scan_range,  # Show detected subnet, not config default
        "scan_range_config": settings.scan_range,  # Original config value
        "detection_method": detection_method,
        "scan_timeout_sec": settings.scan_timeout_sec,
        "scan_concurrency": settings.scan_concurrency,
        "scan_interval_sec": settings.scan_interval_sec,
        "features": {
            "mdns": settings.feature_mdns,
            "ssdp": settings.feature_ssdp,
            "nbns": settings.feature_nbns,
            "snmp": settings.feature_snmp,
            "fingerbank": settings.feature_fingerbank,
            "active_probe": getattr(settings, "feature_active_probe", True),
        },
    }


@router.post(
    "/register",
    response_model=RegisterAdminResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_admin(payload: RegisterAdminRequest):
    """Bootstrap admin account on first run."""
    try:
        token = await setup_service.register_admin(
            username=payload.username, password=payload.password
        )
    except ValueError as e:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from None
    return {"access_token": token, "token_type": "bearer"}


@router.post("/acknowledge", status_code=status.HTTP_204_NO_CONTENT)
async def acknowledge_disclaimer(
    _: AcknowledgeRequest,
    current_user: User = Depends(get_current_admin),
):
    """Mark disclaimer acknowledged and finish first-run gating."""
    await setup_service.acknowledge_disclaimer(username=current_user.username)


@router.post("/replay", status_code=status.HTTP_204_NO_CONTENT)
async def replay_system(current_user: User = Depends(get_current_admin)):
    """Reset app to first-run state and clear volatile data."""
    await reset_service.replay()


@router.get("/lists", response_model=dict[str, list[str]])
async def get_lists(state: StateManager = Depends(get_state_manager)):
    """Get current allow and block lists."""
    return {
        "allow_list": state.get_allow_list(),
        "block_list": state.get_block_list(),
    }


@router.post("/lists/allow", status_code=status.HTTP_204_NO_CONTENT)
async def add_to_allow_list(
    mac: str = Body(
        ..., embed=True, pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
    ),
    admin: User = Depends(get_current_admin),
    state: StateManager = Depends(get_state_manager),
):
    """Add MAC to allow list (Admin only)."""
    state.add_to_allow_list(mac)


@router.post("/lists/block", status_code=status.HTTP_204_NO_CONTENT)
async def add_to_block_list(
    mac: str = Body(
        ..., embed=True, pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
    ),
    admin: User = Depends(get_current_admin),
    state: StateManager = Depends(get_state_manager),
):
    """Add MAC to block list (Admin only)."""
    state.add_to_block_list(mac)


@router.delete("/lists/{mac}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_lists(
    mac: str,
    admin: User = Depends(get_current_admin),
    state: StateManager = Depends(get_state_manager),
):
    """Remove MAC from both allow and block lists (Admin only)."""
    state.remove_from_lists(mac)
