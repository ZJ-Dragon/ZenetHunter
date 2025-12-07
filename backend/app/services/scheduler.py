"""AI Scheduler Service: Orchestrates strategy selection and execution."""

import logging
from typing import Any

from app.models.attack import AttackRequest, AttackType
from app.models.defender import DefenseApplyRequest, DefenseType
from app.models.device import Device
from app.models.scheduler import StrategyFeedback, StrategyIdentifier, StrategyType
from app.services.attack import AttackService
from app.services.defender import DefenderService
from app.services.policy_selector import PolicySelector
from app.services.state import StateManager, get_state_manager
from app.services.telemetry import TelemetryService, get_telemetry_service

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    AI Scheduler Service: Orchestrates strategy selection and execution.
    Integrates PolicySelector with Defense/Attack engines.
    """

    def __init__(
        self,
        state_manager: StateManager | None = None,
        policy_selector: PolicySelector | None = None,
        defender_service: DefenderService | None = None,
        attack_service: AttackService | None = None,
        telemetry_service: TelemetryService | None = None,
        simulation_mode: bool = False,
    ):
        """
        Initialize scheduler service.

        Args:
            state_manager: StateManager instance
            policy_selector: PolicySelector instance
            defender_service: DefenderService instance
            attack_service: AttackService instance
            telemetry_service: TelemetryService instance
            simulation_mode: If True, simulate strategy execution
                without actual engine calls
        """
        self.state = state_manager or get_state_manager()
        self.telemetry = telemetry_service or get_telemetry_service()
        self.selector = policy_selector or PolicySelector(
            state_manager=self.state, telemetry_service=self.telemetry
        )
        self.defender = defender_service or DefenderService()
        self.attack = attack_service or AttackService()
        self.simulation_mode = simulation_mode

    async def execute_strategy_flow(
        self, device_mac: str, max_strategies: int = 3
    ) -> dict[str, Any]:
        """
        Execute a complete strategy flow for a device:
        1. Select strategies using PolicySelector
        2. Apply strategies via Defense/Attack engines
        3. Collect feedback and update scores

        Args:
            device_mac: Target device MAC address
            max_strategies: Maximum number of strategies to apply

        Returns:
            Dictionary with execution results
        """
        device = self.state.get_device(device_mac)
        if not device:
            return {
                "success": False,
                "error": f"Device {device_mac} not found",
            }

        # Step 1: Select strategies
        strategies = self.selector.select_strategy_sequence(device, max_strategies)
        if not strategies:
            return {
                "success": False,
                "error": "No strategies available for device",
            }

        logger.info(
            f"Executing strategy flow for {device_mac}: "
            f"{len(strategies)} strategies selected"
        )

        # Step 2: Apply strategies
        results = []
        previous_strategy = None
        for strategy in strategies:
            # Log strategy switch
            if previous_strategy:
                self.telemetry.log_strategy_switch(
                    device_mac=device.mac,
                    from_strategy=previous_strategy,
                    to_strategy=strategy,
                    reason="Policy selector recommendation",
                )
            previous_strategy = strategy

            result = await self._apply_strategy(device, strategy)
            results.append(result)

            # Log strategy application
            self.telemetry.log_strategy_applied(
                device_mac=device.mac,
                strategy=strategy,
                success=result.get("success", False),
                error=result.get("error"),
            )

        # Step 3: Collect feedback (simulated for now)
        # In a real implementation, we'd monitor device response
        feedback_results = []
        for strategy, result in zip(strategies, results, strict=False):
            if result.get("success"):
                # Simulate feedback collection
                feedback = await self._collect_feedback(
                    device_mac, strategy, result, duration_seconds=60
                )
                if feedback:
                    # Log effectiveness metrics
                    self.telemetry.log_effectiveness(device_mac, strategy, feedback)

                    # Update strategy score
                    self.selector.update_strategy_score(device_mac, strategy, feedback)
                    feedback_results.append(feedback)

        return {
            "success": True,
            "device_mac": device_mac,
            "strategies_applied": len([r for r in results if r.get("success")]),
            "results": results,
            "feedback_collected": len(feedback_results),
        }

    async def _apply_strategy(
        self, device: Device, strategy: StrategyIdentifier
    ) -> dict[str, Any]:
        """
        Apply a single strategy to a device.

        Args:
            device: Target device
            strategy: Strategy to apply

        Returns:
            Result dictionary with success status and details
        """
        try:
            if strategy.type == StrategyType.DEFENSE:
                return await self._apply_defense_strategy(device, strategy)
            elif strategy.type == StrategyType.ATTACK:
                return await self._apply_attack_strategy(device, strategy)
            else:
                return {
                    "success": False,
                    "error": f"Unknown strategy type: {strategy.type}",
                }
        except Exception as e:
            logger.error(f"Failed to apply strategy {strategy.strategy_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "strategy": strategy.strategy_id.value,
            }

    async def _apply_defense_strategy(
        self, device: Device, strategy: StrategyIdentifier
    ) -> dict[str, Any]:
        """Apply a defense strategy."""
        if not isinstance(strategy.strategy_id, DefenseType):
            return {"success": False, "error": "Invalid defense strategy type"}

        defense_type: DefenseType = strategy.strategy_id

        if self.simulation_mode:
            logger.info(
                f"[SIMULATION] Applying defense {defense_type.value} to {device.mac}"
            )
            return {
                "success": True,
                "strategy": strategy.strategy_id.value,
                "type": "defense",
                "simulated": True,
            }

        # Apply via DefenderService
        request = DefenseApplyRequest(policy=defense_type)
        try:
            await self.defender.apply_defense(device.mac, request)
            return {
                "success": True,
                "strategy": strategy.strategy_id.value,
                "type": "defense",
            }
        except Exception as e:
            logger.error(f"Defense application failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "strategy": strategy.strategy_id.value,
            }

    async def _apply_attack_strategy(
        self, device: Device, strategy: StrategyIdentifier
    ) -> dict[str, Any]:
        """Apply an attack strategy."""
        if not isinstance(strategy.strategy_id, AttackType):
            return {"success": False, "error": "Invalid attack strategy type"}

        attack_type: AttackType = strategy.strategy_id

        if self.simulation_mode:
            logger.info(
                f"[SIMULATION] Applying attack {attack_type.value} to {device.mac}"
            )
            return {
                "success": True,
                "strategy": strategy.strategy_id.value,
                "type": "attack",
                "simulated": True,
            }

        # Apply via AttackService
        request = AttackRequest(type=attack_type, duration=60)
        try:
            response = await self.attack.start_attack(device.mac, request)
            return {
                "success": response.status.value != "failed",
                "strategy": strategy.strategy_id.value,
                "type": "attack",
                "status": response.status.value,
                "message": response.message,
            }
        except Exception as e:
            logger.error(f"Attack application failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "strategy": strategy.strategy_id.value,
            }

    async def _collect_feedback(
        self,
        device_mac: str,
        strategy: StrategyIdentifier,
        result: dict[str, Any],
        duration_seconds: int = 60,
    ) -> StrategyFeedback | None:
        """
        Collect feedback on strategy effectiveness.
        In simulation mode, generates synthetic feedback.
        In real mode, would monitor device response.

        Args:
            device_mac: Device MAC address
            strategy: Strategy that was applied
            result: Result from strategy application
            duration_seconds: How long strategy was active

        Returns:
            StrategyFeedback or None if collection failed
        """
        if self.simulation_mode:
            # Generate synthetic feedback for simulation
            # Simulate different effectiveness based on strategy type
            if strategy.type == StrategyType.DEFENSE:
                # Defense strategies generally have good effectiveness
                effect_score = 0.7
                resource_cost = 0.3
                device_response = "restricted"
            else:
                # Attack strategies may vary
                effect_score = 0.6
                resource_cost = 0.4
                device_response = "disconnected"

            # Add some randomness
            import random

            effect_score += random.uniform(-0.1, 0.1)
            effect_score = max(0.0, min(1.0, effect_score))

            return StrategyFeedback(
                device_mac=device_mac,
                strategy=strategy,
                effect_score=effect_score,
                resource_cost=resource_cost,
                duration_seconds=duration_seconds,
                device_response=device_response,
            )

        # Real mode: would monitor device state and network metrics
        # For now, return None (feedback collection not implemented)
        logger.warning(
            "Real feedback collection not implemented. "
            "Using simulation mode or implement monitoring."
        )
        return None

    async def simulate_complete_flow(self, device_mac: str) -> dict[str, Any]:
        """
        Simulate a complete strategy flow for testing/demonstration.

        Args:
            device_mac: Target device MAC address

        Returns:
            Complete flow results
        """
        # Create a simulation scheduler
        sim_scheduler = SchedulerService(
            state_manager=self.state,
            policy_selector=self.selector,
            simulation_mode=True,
        )

        return await sim_scheduler.execute_strategy_flow(device_mac, max_strategies=3)


# Global instance (singleton pattern)
_scheduler_instance: SchedulerService | None = None


def get_scheduler_service() -> SchedulerService:
    """Get global SchedulerService instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SchedulerService()
    return _scheduler_instance
