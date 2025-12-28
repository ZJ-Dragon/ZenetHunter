from typing import Any

from fastapi import APIRouter, Depends, Path, status

from app.models.scheduler import StrategyFeedback
from app.services.scheduler import SchedulerService, get_scheduler_service

router = APIRouter(tags=["scheduler"])


@router.post(
    "/devices/{mac}/scheduler/execute",
    summary="Execute AI strategy flow",
    status_code=status.HTTP_200_OK,
)
async def execute_strategy_flow(
    mac: str = Path(..., title="Device MAC address"),
    max_strategies: int = 3,
    service: SchedulerService = Depends(get_scheduler_service),
) -> dict[str, Any]:
    """
    Manually trigger the AI strategy scheduler for a specific device.
    This will:
    1. Analyze device state
    2. Select best strategies using Rule+RL engine
    3. Apply strategies (or simulate if configured)
    4. Return results
    """
    return await service.execute_strategy_flow(mac, max_strategies=max_strategies)


@router.post(
    "/devices/{mac}/scheduler/simulate",
    summary="Simulate AI strategy flow",
    status_code=status.HTTP_200_OK,
)
async def simulate_strategy_flow(
    mac: str = Path(..., title="Device MAC address"),
    service: SchedulerService = Depends(get_scheduler_service),
) -> dict[str, Any]:
    """
    Simulate the AI strategy flow without actually applying changes.
    Useful for testing the decision engine.
    """
    return await service.simulate_complete_flow(mac)


@router.post(
    "/devices/{mac}/scheduler/feedback",
    summary="Submit strategy feedback",
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_feedback(
    feedback: StrategyFeedback,
    mac: str = Path(..., title="Device MAC address"),
    service: SchedulerService = Depends(get_scheduler_service),
) -> dict[str, str]:
    """
    Submit manual feedback for a strategy application.
    This helps train the RL model.
    """
    # Verify MAC matches
    if feedback.device_mac != mac:
        return {"error": "MAC address mismatch"}

    # Update score
    service.selector.update_strategy_score(mac, feedback.strategy, feedback)
    return {"status": "accepted", "message": "Feedback recorded"}
