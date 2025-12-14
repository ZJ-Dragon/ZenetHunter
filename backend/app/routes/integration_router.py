from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.exceptions import AppError, ErrorCode
from app.core.security import get_current_admin
from app.models.auth import User
from app.models.router_integration import (
    ACLRule,
    IsolationPolicy,
    RateLimitPolicy,
    RouterActionResult,
)
from app.services.router import RouterService, get_router_service

router = APIRouter(tags=["integration", "router"])


@router.post(
    "/integration/router/rate-limit",
    response_model=RouterActionResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def set_rate_limit(
    policy: RateLimitPolicy,
    admin: Annotated[User, Depends(get_current_admin)],
    service: RouterService = Depends(get_router_service),
):
    result = await service.set_rate_limit(policy)
    if result.status == "failed":
        raise AppError(ErrorCode.API_BAD_REQUEST, result.message or "rate limit failed")
    return result


@router.delete(
    "/integration/router/rate-limit/{mac}",
    response_model=RouterActionResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def remove_rate_limit(
    mac: str,
    admin: Annotated[User, Depends(get_current_admin)],
    service: RouterService = Depends(get_router_service),
):
    result = await service.remove_rate_limit(mac)
    if result.status == "failed":
        raise AppError(ErrorCode.API_BAD_REQUEST, result.message or "remove failed")
    return result


@router.post(
    "/integration/router/acl",
    response_model=RouterActionResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def apply_acl(
    rule: ACLRule,
    admin: Annotated[User, Depends(get_current_admin)],
    service: RouterService = Depends(get_router_service),
):
    result = await service.apply_acl_rule(rule)
    return result


@router.delete(
    "/integration/router/acl/{rule_id}",
    response_model=RouterActionResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def remove_acl(
    rule_id: str,
    admin: Annotated[User, Depends(get_current_admin)],
    service: RouterService = Depends(get_router_service),
):
    result = await service.remove_acl_rule(rule_id)
    if result.status == "failed":
        raise AppError(ErrorCode.API_BAD_REQUEST, result.message or "remove failed")
    return result


@router.post(
    "/integration/router/isolate",
    response_model=RouterActionResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def isolate_device(
    policy: IsolationPolicy,
    admin: Annotated[User, Depends(get_current_admin)],
    service: RouterService = Depends(get_router_service),
):
    result = await service.isolate_device(policy)
    if result.status == "failed":
        raise AppError(ErrorCode.API_BAD_REQUEST, result.message or "isolate failed")
    return result


@router.post(
    "/integration/router/reintegrate/{mac}",
    response_model=RouterActionResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def reintegrate_device(
    mac: str,
    admin: Annotated[User, Depends(get_current_admin)],
    service: RouterService = Depends(get_router_service),
):
    result = await service.reintegrate_device(mac)
    if result.status == "failed":
        raise AppError(
            ErrorCode.API_BAD_REQUEST, result.message or "reintegrate failed"
        )
    return result
