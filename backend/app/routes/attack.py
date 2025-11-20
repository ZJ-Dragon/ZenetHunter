from fastapi import APIRouter, Depends, status

from app.core.exceptions import AppError, ErrorCode
from app.models.attack import AttackRequest, AttackResponse
from app.services.attack import AttackService, get_attack_service

router = APIRouter(tags=["attack"])


@router.post(
    "/devices/{mac}/attack",
    response_model=AttackResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_attack(
    mac: str,
    request: AttackRequest,
    service: AttackService = Depends(get_attack_service),
):
    """Start an attack on a specific device."""
    response = await service.start_attack(mac, request)
    if response.status == "failed":
        raise AppError(ErrorCode.API_BAD_REQUEST, response.message or "Attack failed")
    return response


@router.post(
    "/devices/{mac}/attack/stop",
    response_model=AttackResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def stop_attack(
    mac: str,
    service: AttackService = Depends(get_attack_service),
):
    """Stop an attack on a specific device."""
    response = await service.stop_attack(mac)
    if response.status == "failed":
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND, response.message or "Device not found"
        )
    return response
