"""Dummy attack engine for testing and fallback."""

import asyncio
import logging

from app.core.engine.base import AttackEngine
from app.models.attack import AttackType

logger = logging.getLogger(__name__)


class DummyAttackEngine(AttackEngine):
    """Dummy engine that simulates attacks with logging."""

    def check_permissions(self) -> bool:
        """Dummy engine always runs (safe)."""
        return True

    async def start_attack(
        self, target_mac: str, attack_type: AttackType, duration: int
    ) -> None:
        """Simulate starting an attack."""
        logger.info(
            f"[DummyEngine] Starting {attack_type} on {target_mac} for {duration}s"
        )
        # In a real engine, this would spawn a process or send packets.
        # Here we just log and let the service handle the 'duration' sleep.
        # However, if the engine is responsible for the loop, we would do it here.
        # For the 'kick' type, it usually runs for a duration.
        
        # Simulate some work if needed, but usually the service controls lifecycle via async tasks.
        # We'll just log.
        pass

    async def stop_attack(self, target_mac: str) -> None:
        """Simulate stopping an attack."""
        logger.info(f"[DummyEngine] Stopping attack on {target_mac}")
        pass

