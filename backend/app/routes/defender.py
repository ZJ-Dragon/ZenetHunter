from fastapi import APIRouter, Depends, Path, status

from app.models.defender import DefenseApplyRequest, DefensePolicy, DefenseResponse, DefenseStatus
from app.services.defender import DefenderService

router = APIRouter(tags=["defense"])


def get_defender_service() -> DefenderService:
    return DefenderService()


@router.get(
    "/defense/policies",
    response_model=list[DefensePolicy],
    summary="Get available defense policies",
)
async def get_policies(
    service: DefenderService = Depends(get_defender_service),
) -> list[DefensePolicy]:
    """List all available defense policies and strategies."""
    return service.get_policies()


@router.post(
    "/devices/{mac}/defense/apply",
    response_model=DefenseResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Apply defense policy to a device",
)
async def apply_defense(
    request: DefenseApplyRequest,
    mac: str = Path(..., title="Device MAC address", pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"),
    service: DefenderService = Depends(get_defender_service),
) -> DefenseResponse:
    """
    Start or update a defense mechanism on a specific device.
    This action is asynchronous and may take time to fully propagate.
    """
    await service.apply_defense(mac, request)
    return DefenseResponse(
        device_mac=mac,
        status=DefenseStatus.ACTIVE,
        active_policy=request.policy,
        message="Defense policy applied successfully",
    )


@router.post(
    "/devices/{mac}/defense/stop",
    response_model=DefenseResponse,
    summary="Stop defense on a device",
)
async def stop_defense(
    mac: str = Path(..., title="Device MAC address", pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"),
    service: DefenderService = Depends(get_defender_service),
) -> DefenseResponse:
    """Stop any active defense mechanism on a specific device."""
    await service.stop_defense(mac)
    return DefenseResponse(
        device_mac=mac,
        status=DefenseStatus.INACTIVE,
        message="Defense stopped",
    )

