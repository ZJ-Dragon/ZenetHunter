from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, Field

from app.core.exceptions import AppError, ErrorCode
from app.core.security import get_current_user
from app.models.auth import User
from app.models.defender import (
    DefenseApplyRequest,
    DefensePolicy,
    DefenseResponse,
    DefenseStatus,
)
from app.models.scheduler import StrategyIdentifier
from app.services.defender import DefenderService
from app.services.policy_selector import PolicySelector, get_policy_selector
from app.services.state import get_state_manager

router = APIRouter(tags=["defense"])


class AutoDefenseRequest(BaseModel):
    """Request for automatic defense strategy selection."""

    max_strategies: int = Field(
        default=3, ge=1, le=10, description="Maximum number of strategies to apply"
    )


class AutoDefenseResponse(BaseModel):
    """Response for automatic defense."""

    device_mac: str = Field(..., description="Target device MAC")
    strategies_applied: list[str] = Field(
        ..., description="List of applied strategy IDs"
    )
    count: int = Field(..., description="Number of strategies applied")
    message: str = Field(..., description="Status message")


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
    mac: str = Path(
        ...,
        title="Device MAC address",
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
    ),
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
    mac: str = Path(
        ...,
        title="Device MAC address",
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
    ),
    service: DefenderService = Depends(get_defender_service),
) -> DefenseResponse:
    """Stop any active defense mechanism on a specific device."""
    await service.stop_defense(mac)
    return DefenseResponse(
        device_mac=mac,
        status=DefenseStatus.INACTIVE,
        message="Defense stopped",
    )


@router.post(
    "/devices/{mac}/defense/auto",
    response_model=AutoDefenseResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Automatically select and apply defense strategies (AI-driven)",
)
async def auto_defense(
    mac: str = Path(
        ...,
        title="Device MAC address",
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
    ),
    request: AutoDefenseRequest = AutoDefenseRequest(),
    current_user: User = Depends(get_current_user),
    selector: PolicySelector = Depends(get_policy_selector),
    state_manager=Depends(get_state_manager),
) -> AutoDefenseResponse:
    """
    Automatically select and apply the best defense/attack strategies for a device.

    This endpoint uses AI-driven policy selection based on:
    - Device characteristics (type, status, history)
    - Q-learning based strategy effectiveness
    - Rule-based heuristics
    - Strategy cooldowns and backoff factors

    The system will prioritize defense strategies over attack strategies,
    and will automatically learn from feedback to improve future selections.
    """
    # Get device
    device = state_manager.get_device(mac)
    if not device:
        raise AppError(
            ErrorCode.CONFIG_NOT_FOUND,
            f"Device with MAC {mac} not found",
            extra={"mac": mac},
        )

    # Auto-select and apply strategies
    applied_strategies = await selector.auto_select_and_apply(
        device, max_strategies=request.max_strategies
    )

    strategy_ids = [s.strategy_id.value for s in applied_strategies]

    return AutoDefenseResponse(
        device_mac=mac,
        strategies_applied=strategy_ids,
        count=len(applied_strategies),
        message=(
            f"Automatically applied {len(applied_strategies)} "
            f"strategies to device {mac}"
        ),
    )


class StrategyFeedbackRequest(BaseModel):
    """Request for strategy feedback."""

    strategy_type: str = Field(..., description="Strategy type: 'defense' or 'attack'")
    strategy_id: str = Field(..., description="Strategy ID (e.g., 'block_wan', 'kick')")
    effect_score: float = Field(
        ..., ge=0.0, le=1.0, description="Effectiveness score (0.0-1.0)"
    )
    resource_cost: float = Field(
        ..., ge=0.0, le=1.0, description="Resource cost (0.0-1.0)"
    )
    duration_seconds: int = Field(
        default=0, ge=0, description="How long the strategy was active"
    )
    device_response: str | None = Field(None, description="Observed device response")


@router.post(
    "/devices/{mac}/defense/feedback",
    status_code=status.HTTP_200_OK,
    summary="Submit feedback on defense/attack strategy effectiveness",
)
async def submit_strategy_feedback(
    mac: str = Path(
        ...,
        title="Device MAC address",
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
    ),
    request: StrategyFeedbackRequest = ...,
    current_user: User = Depends(get_current_user),
    selector: PolicySelector = Depends(get_policy_selector),
) -> dict:
    """
    Submit feedback on the effectiveness of a defense or attack strategy.

    This feedback is used by the AI scheduler to improve future strategy selection:
    - Updates Q-learning Q-table values
    - Adjusts strategy backoff factors
    - Sets cooldown periods for ineffective strategies

    Args:
        mac: Device MAC address
        request: Feedback request with strategy details and effectiveness scores
    """
    from app.models.attack import AttackType
    from app.models.defender import DefenseType
    from app.models.scheduler import StrategyFeedback, StrategyType

    # Create strategy identifier
    try:
        strategy_type_enum = StrategyType(request.strategy_type.lower())

        # Convert strategy_id string to enum
        if strategy_type_enum == StrategyType.DEFENSE:
            strategy_id_enum = DefenseType(request.strategy_id)
        else:
            strategy_id_enum = AttackType(request.strategy_id)

        strategy = StrategyIdentifier(
            type=strategy_type_enum, strategy_id=strategy_id_enum
        )
    except (ValueError, KeyError) as e:
        raise AppError(
            ErrorCode.API_BAD_REQUEST, f"Invalid strategy type or ID: {e}"
        ) from e

    # Create feedback
    feedback = StrategyFeedback(
        device_mac=mac,
        strategy=strategy,
        effect_score=request.effect_score,
        resource_cost=request.resource_cost,
        duration_seconds=request.duration_seconds,
        device_response=request.device_response,
        timestamp=datetime.now(UTC),
    )

    # Update strategy score
    selector.update_strategy_score(mac, strategy, feedback)

    return {
        "message": "Feedback submitted successfully",
        "device_mac": mac,
        "strategy": request.strategy_id,
        "effect_score": request.effect_score,
        "resource_cost": request.resource_cost,
    }
