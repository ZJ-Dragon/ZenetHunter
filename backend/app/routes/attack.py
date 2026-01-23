"""Active Defense API Routes.

This module provides REST API endpoints for active defense operations
in network security research environments.

⚠️  AUTHORIZED USE ONLY ⚠️
All endpoints require authentication and are intended for authorized
security research and testing purposes only.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppError, ErrorCode
from app.core.security import get_current_user
from app.models.attack import (
    ActiveDefenseRequest,
    ActiveDefenseResponse,
    ActiveDefenseType,
)
from app.models.auth import User
from app.repositories.device import DeviceRepository
from app.services.attack import get_active_defense_service

router = APIRouter(
    prefix="/active-defense",
    tags=["Active Defense"],
    responses={
        401: {"description": "Unauthorized - Authentication required"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Target device not found"},
    },
)


@router.get(
    "/types",
    response_model=list[dict],
    summary="List available active defense types",
    description=(
        "Get a list of all available active defense strategies "
        "with descriptions"
    ),
)
async def list_defense_types(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[dict]:
    """List all available active defense operation types.

    Returns a comprehensive list of supported active defense strategies,
    including their identifiers, names, and descriptions.
    """
    defense_types = []
    for defense_type in ActiveDefenseType:
        defense_types.append(
            {
                "id": defense_type.value,
                "name": defense_type.name,
                "description": _get_defense_description(defense_type),
            }
        )
    return defense_types


def _get_defense_description(defense_type: ActiveDefenseType) -> str:
    """Get human-readable description for a defense type."""
    descriptions = {
        ActiveDefenseType.KICK: (
            "WiFi Deauthentication - Disconnect device from network"
        ),
        ActiveDefenseType.BLOCK: "ARP Spoofing - Redirect or block device traffic",
        ActiveDefenseType.ARP_FLOOD: "ARP Flooding - Stress test network ARP tables",
        ActiveDefenseType.DHCP_SPOOF: "DHCP Spoofing - Control IP address assignment",
        ActiveDefenseType.DNS_SPOOF: "DNS Spoofing - Redirect DNS queries",
        ActiveDefenseType.ICMP_REDIRECT: "ICMP Redirect - Manipulate routing tables",
        ActiveDefenseType.MAC_FLOOD: "MAC Flooding - Test switch CAM table limits",
        ActiveDefenseType.VLAN_HOP: "VLAN Hopping - Test network segmentation",
        ActiveDefenseType.BEACON_FLOOD: "Beacon Flooding - WiFi AP confusion testing",
        ActiveDefenseType.PORT_SCAN: "Port Scanning - Active service discovery",
        ActiveDefenseType.TRAFFIC_SHAPE: "Traffic Shaping - Bandwidth control testing",
        ActiveDefenseType.SYN_FLOOD: "SYN Flooding - TCP connection exhaustion testing",
        ActiveDefenseType.UDP_FLOOD: "UDP Flooding - Bandwidth exhaustion testing",
        ActiveDefenseType.TCP_RST: "TCP RST Injection - Connection termination testing",
    }
    return descriptions.get(defense_type, "Active defense operation")


@router.post(
    "/{mac}/start",
    response_model=ActiveDefenseResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start active defense operation",
    description="Initiate an active defense operation on a specific target device",
)
async def start_operation(
    mac: str = Path(
        ...,
        description="Target device MAC address",
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
        example="aa:bb:cc:dd:ee:ff",
    ),
    request: ActiveDefenseRequest = ...,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    service=Depends(get_active_defense_service),
    db: AsyncSession = Depends(get_db),
) -> ActiveDefenseResponse:
    """Start an active defense operation on a target device.

    This endpoint initiates an active defense operation with the specified
    parameters. The operation runs asynchronously in the background.

    Args:
        mac: Target device MAC address (format: aa:bb:cc:dd:ee:ff)
        request: Operation parameters (type, duration, intensity)
        current_user: Authenticated user (injected)
        service: Active defense service (injected)
        db: Database session (injected)

    Returns:
        ActiveDefenseResponse with operation status and details

    Raises:
        AppError: If the operation fails to start
    """
    response = await service.start_operation(mac, request)
    if response.status == "failed":
        raise AppError(
            ErrorCode.API_BAD_REQUEST,
            response.message or "Failed to start active defense operation",
        )

    # Update device status in database
    repo = DeviceRepository(db)
    await repo.update_attack_status(mac, response.status)
    await db.commit()

    return response


@router.post(
    "/{mac}/stop",
    response_model=ActiveDefenseResponse,
    status_code=status.HTTP_200_OK,
    summary="Stop active defense operation",
    description="Stop any active defense operation running on the target device",
)
async def stop_operation(
    mac: str = Path(
        ...,
        description="Target device MAC address",
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
        example="aa:bb:cc:dd:ee:ff",
    ),
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    service=Depends(get_active_defense_service),
    db: AsyncSession = Depends(get_db),
) -> ActiveDefenseResponse:
    """Stop an active defense operation on a target device.

    This endpoint immediately stops any running active defense operation
    on the specified device and performs cleanup.

    Args:
        mac: Target device MAC address
        current_user: Authenticated user (injected)
        service: Active defense service (injected)
        db: Database session (injected)

    Returns:
        ActiveDefenseResponse with stop status

    Raises:
        AppError: If the device is not found
    """
    response = await service.stop_operation(mac)
    if response.status == "failed":
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND, response.message or "Target device not found"
        )

    # Update device status in database
    repo = DeviceRepository(db)
    await repo.update_attack_status(mac, response.status)
    await db.commit()

    return response


# Legacy compatibility endpoints (will be deprecated)
@router.post(
    "/devices/{mac}/attack",
    response_model=ActiveDefenseResponse,
    status_code=status.HTTP_202_ACCEPTED,
    deprecated=True,
    summary="[DEPRECATED] Start attack (legacy)",
    description="Legacy endpoint. Use POST /active-defense/{mac}/start instead",
    include_in_schema=False,
)
async def legacy_start_attack(
    mac: str,
    request: ActiveDefenseRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service=Depends(get_active_defense_service),
    db: AsyncSession = Depends(get_db),
):
    """Legacy endpoint for backward compatibility."""
    return await start_operation(mac, request, current_user, service, db)


@router.post(
    "/devices/{mac}/attack/stop",
    response_model=ActiveDefenseResponse,
    status_code=status.HTTP_200_OK,
    deprecated=True,
    summary="[DEPRECATED] Stop attack (legacy)",
    description="Legacy endpoint. Use POST /active-defense/{mac}/stop instead",
    include_in_schema=False,
)
async def legacy_stop_attack(
    mac: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service=Depends(get_active_defense_service),
    db: AsyncSession = Depends(get_db),
):
    """Legacy endpoint for backward compatibility."""
    return await stop_operation(mac, current_user, service, db)
