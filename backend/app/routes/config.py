from fastapi import APIRouter, Body, Depends, status

from app.core.security import get_current_admin
from app.models.auth import User
from app.services.state import StateManager, get_state_manager

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/status")
async def get_config_status(state: StateManager = Depends(get_state_manager)):
    """
    Check if system is configured (OOBE check).

    For MVP: Always returns is_configured=True to allow immediate login
    with default credentials.
    Users can login with admin/zenethunter without going through setup wizard.

    In future: Should check DB for admin user existence to determine if setup is needed.
    """
    # MVP: Always return configured - users can login with default
    # credentials immediately
    # This allows users to bypass setup wizard and use default admin/zenethunter
    return {
        "is_configured": True,
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
            "active_probe": getattr(settings, "feature_active_probe", True),
            "http_ident": getattr(settings, "feature_http_ident", True),
            "printer_ident": getattr(settings, "feature_printer_ident", True),
        },
    }


@router.post("/setup", status_code=status.HTTP_204_NO_CONTENT)
async def setup_system(
    data: dict = Body(...),
    state: StateManager = Depends(get_state_manager),
):
    """
    Initial system setup (OOBE).
    Creates admin account and configures basic settings.
    This endpoint does NOT require authentication (called during initial setup).

    For MVP, this is a placeholder - admin account creation will be implemented later.
    Currently accepts setup data but doesn't persist admin credentials.
    Users can still login with default credentials (admin/zenethunter).
    """
    # MVP Implementation: Setup wizard accepts configuration but uses
    # default credentials. For production deployment, admin user creation
    # with hashed passwords should be implemented
    # Current behavior: Users login with default credentials (admin/zenethunter)
    # Future enhancement: Create admin user in database with bcrypt-hashed password
    _ = data.get("admin_password", "")  # Reserved for future implementation
    _ = data.get("target_subnets", [])  # Reserved for scan configuration
    _ = data.get("scan_interval", 300)  # Reserved for auto-scan intervals
    _ = data.get("default_policy", "monitor")  # Reserved for default policy

    # Log setup completion (in future, persist to DB)
    # For now, setup is considered complete if this endpoint is called successfully


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
