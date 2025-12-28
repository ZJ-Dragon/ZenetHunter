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
    # MVP: Placeholder - in future, create admin user in DB with hashed password
    # For now, just accept the setup request
    # The admin_password from data will be used in future to create admin user
    # TODO: Implement admin user creation with password hashing in DB
    # These variables are kept for future use
    _ = data.get("admin_password", "")
    _ = data.get("target_subnets", [])
    _ = data.get("scan_interval", 300)
    _ = data.get("default_policy", "monitor")

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
