import logging
from typing import Any

from app.core.engine.base_defense import DefenseEngine
from app.models.defender import DefenseType

logger = logging.getLogger(__name__)


class DummyDefenseEngine(DefenseEngine):
    """Safe, log-only defense engine."""

    def check_capabilities(self) -> bool:
        """Always returns True for dummy engine."""
        return True

    async def apply_policy(
        self, target: str, policy: DefenseType, params: dict[str, Any] | None = None
    ) -> None:
        logger.info(
            f"[DummyDefense] Applying {policy} to {target} with params: {params}"
        )

    async def remove_policy(self, target: str, policy: DefenseType) -> None:
        logger.info(f"[DummyDefense] Removing {policy} from {target}")

    async def enable_global_protection(self, policy: DefenseType) -> None:
        logger.info(f"[DummyDefense] Enabling global protection: {policy}")
        if policy == DefenseType.SYN_PROXY:
            logger.info("[DummyDefense] SYNPROXY simulation enabled.")
        elif policy == DefenseType.UDP_RATE_LIMIT:
            logger.info("[DummyDefense] UDP Rate Limit simulation enabled (tc qdisc).")
        elif policy == DefenseType.TCP_RESET_POLICY:
            logger.info(
                "[DummyDefense] TCP Reset Policy simulation enabled "
                "(iptables REJECT with tcp-reset)."
            )
        elif policy == DefenseType.WALLED_GARDEN:
            logger.info(
                "[DummyDefense] Walled Garden simulation enabled "
                "(HTTP/HTTPS redirect to Portal)."
            )

    async def disable_global_protection(self, policy: DefenseType) -> None:
        logger.info(f"[DummyDefense] Disabling global protection: {policy}")
