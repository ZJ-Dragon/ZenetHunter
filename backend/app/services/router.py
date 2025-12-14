import logging

from app.core.engine.router_factory import get_router_manager
from app.models.router_integration import (
    ACLRule,
    ActionStatus,
    IsolationPolicy,
    RateLimitPolicy,
    RouterActionResult,
)

logger = logging.getLogger(__name__)


class RouterService:
    """Service layer wrapping RouterManager adapter with app-friendly results."""

    def __init__(self) -> None:
        self.manager = get_router_manager()

    # ---- Rate limit --------------------------------------------------------
    async def set_rate_limit(self, policy: RateLimitPolicy) -> RouterActionResult:
        ok = await self.manager.set_rate_limit(policy)
        return RouterActionResult(
            status=ActionStatus.SUCCESS if ok else ActionStatus.FAILED,
            message=(
                f"Rate limit applied for {policy.target_mac}"
                if ok
                else "Failed to apply rate limit"
            ),
        )

    async def remove_rate_limit(self, target_mac: str) -> RouterActionResult:
        ok = await self.manager.remove_rate_limit(target_mac)
        return RouterActionResult(
            status=ActionStatus.SUCCESS if ok else ActionStatus.FAILED,
            message=(
                f"Rate limit removed for {target_mac}"
                if ok
                else "Failed to remove rate limit"
            ),
        )

    # ---- ACL ---------------------------------------------------------------
    async def apply_acl_rule(self, rule: ACLRule) -> RouterActionResult:
        rule_id = await self.manager.apply_acl_rule(rule)
        return RouterActionResult(
            status=ActionStatus.SUCCESS,
            message="ACL rule applied",
            data={"rule_id": rule_id},
        )

    async def remove_acl_rule(self, rule_id: str) -> RouterActionResult:
        ok = await self.manager.remove_acl_rule(rule_id)
        return RouterActionResult(
            status=ActionStatus.SUCCESS if ok else ActionStatus.FAILED,
            message=(
                f"ACL rule {rule_id} removed"
                if ok
                else f"ACL rule {rule_id} not removed"
            ),
        )

    # ---- Isolation ---------------------------------------------------------
    async def isolate_device(self, policy: IsolationPolicy) -> RouterActionResult:
        ok = await self.manager.isolate_device(policy)
        return RouterActionResult(
            status=ActionStatus.SUCCESS if ok else ActionStatus.FAILED,
            message=(
                f"Device {policy.target_mac} isolated"
                if ok
                else "Failed to isolate device"
            ),
        )

    async def reintegrate_device(self, target_mac: str) -> RouterActionResult:
        ok = await self.manager.reintegrate_device(target_mac)
        return RouterActionResult(
            status=ActionStatus.SUCCESS if ok else ActionStatus.FAILED,
            message=(
                f"Device {target_mac} reintegrated"
                if ok
                else "Failed to reintegrate device"
            ),
        )


def get_router_service() -> RouterService:
    return RouterService()
