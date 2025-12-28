from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppError, ErrorCode
from app.core.security import get_current_user
from app.models.attack import AttackRequest, AttackResponse
from app.models.auth import User
from app.repositories.device import DeviceRepository
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
    current_user: Annotated[User, Depends(get_current_user)],
    service: AttackService = Depends(get_attack_service),
    db: AsyncSession = Depends(get_db),
):
    """Start an attack on a specific device."""
    response = await service.start_attack(mac, request)
    if response.status == "failed":
        raise AppError(ErrorCode.API_BAD_REQUEST, response.message or "Attack failed")

    # Update device attack status in database
    repo = DeviceRepository(db)
    await repo.update_attack_status(mac, response.status)
    await db.commit()

    return response


@router.post(
    "/devices/{mac}/attack/start",
    response_model=AttackResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_attack_alias(
    mac: str,
    request: AttackRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: AttackService = Depends(get_attack_service),
    db: AsyncSession = Depends(get_db),
):
    """Alias for /devices/{mac}/attack endpoint."""
    response = await service.start_attack(mac, request)
    if response.status == "failed":
        raise AppError(ErrorCode.API_BAD_REQUEST, response.message or "Attack failed")

    # Update device attack status in database
    repo = DeviceRepository(db)
    await repo.update_attack_status(mac, response.status)
    await db.commit()

    return response


@router.post(
    "/devices/{mac}/attack/stop",
    response_model=AttackResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def stop_attack(
    mac: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: AttackService = Depends(get_attack_service),
    db: AsyncSession = Depends(get_db),
):
    """Stop an attack on a specific device."""
    response = await service.stop_attack(mac)
    if response.status == "failed":
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND, response.message or "Device not found"
        )

    # Update device attack status in database
    repo = DeviceRepository(db)
    await repo.update_attack_status(mac, response.status)
    await db.commit()

    return response
