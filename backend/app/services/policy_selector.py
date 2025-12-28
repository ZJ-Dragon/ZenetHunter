"""Policy Selector Service: Rule-based + Lightweight RL Strategy Selection."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from app.models.attack import AttackType
from app.models.defender import DefenseType
from app.models.device import Device
from app.models.scheduler import (
    StrategyFeedback,
    StrategyIdentifier,
    StrategyScore,
    StrategyType,
)
from app.services.qtable_persistence import QTablePersistence
from app.services.state import StateManager, get_state_manager
from app.services.telemetry import TelemetryService, get_telemetry_service

logger = logging.getLogger(__name__)


class StrategyCooldown:
    """Tracks cooldown periods for strategies."""

    def __init__(self):
        self._cooldowns: dict[str, datetime] = {}  # key: strategy_key, value: until

    def is_on_cooldown(self, strategy: StrategyIdentifier) -> bool:
        """Check if strategy is on cooldown."""
        key = self._make_key(strategy)
        until = self._cooldowns.get(key)
        if until is None:
            return False
        if datetime.now(UTC) >= until:
            del self._cooldowns[key]
            return False
        return True

    def set_cooldown(self, strategy: StrategyIdentifier, duration_seconds: int) -> None:
        """Set cooldown for a strategy."""
        key = self._make_key(strategy)
        self._cooldowns[key] = datetime.now(UTC) + timedelta(seconds=duration_seconds)

    def get_remaining_cooldown(self, strategy: StrategyIdentifier) -> int | None:
        """Get remaining cooldown in seconds, or None if not on cooldown."""
        key = self._make_key(strategy)
        until = self._cooldowns.get(key)
        if until is None:
            return None
        remaining = (until - datetime.now(UTC)).total_seconds()
        if remaining <= 0:
            del self._cooldowns[key]
            return None
        return int(remaining)

    def _make_key(self, strategy: StrategyIdentifier) -> str:
        """Generate key for strategy."""
        return f"{strategy.type.value}:{strategy.strategy_id.value}"


class StrategyBackoff:
    """Manages backoff logic for strategies based on effectiveness."""

    def __init__(self):
        self._backoff_factors: dict[str, float] = {}  # key: strategy_key, value: factor

    def get_backoff_factor(self, strategy: StrategyIdentifier) -> float:
        """Get backoff factor (0.0-1.0) for a strategy."""
        key = self._make_key(strategy)
        return self._backoff_factors.get(key, 1.0)

    def update_backoff(
        self,
        strategy: StrategyIdentifier,
        effect_score: float,
        base_factor: float = 0.9,
    ) -> None:
        """
        Update backoff factor based on effectiveness.
        Lower effect_score -> higher backoff (reduce usage).
        """
        key = self._make_key(strategy)
        current = self._backoff_factors.get(key, 1.0)

        # If strategy was ineffective, increase backoff
        if effect_score < 0.3:
            new_factor = current * base_factor  # Reduce by 10%
        elif effect_score > 0.7:
            # If effective, gradually reduce backoff
            new_factor = min(1.0, current * 1.1)  # Increase by 10%, cap at 1.0
        else:
            # Moderate effectiveness, keep current
            new_factor = current

        self._backoff_factors[key] = new_factor
        logger.debug(f"Updated backoff for {key}: {current:.2f} -> {new_factor:.2f}")

    def _make_key(self, strategy: StrategyIdentifier) -> str:
        """Generate key for strategy."""
        return f"{strategy.type.value}:{strategy.strategy_id.value}"


class PolicySelector:
    """
    Policy Selector: Rule-based + Lightweight RL for strategy selection.
    Prioritizes defense strategies over attack strategies.
    """

    # Defense strategies (ordered by priority/preference)
    DEFENSE_STRATEGIES = [
        DefenseType.UDP_RATE_LIMIT,  # Lightweight, low resource cost
        DefenseType.TCP_RESET_POLICY,  # Quick response
        DefenseType.WALLED_GARDEN,  # User-friendly restriction
        DefenseType.DNS_RPZ,  # DNS-level blocking
        DefenseType.SYN_PROXY,  # Gateway-level protection
        DefenseType.TARPIT,  # Resource-consuming for attacker
        DefenseType.ARP_DAI,  # Network-level protection
        DefenseType.BLOCK_WAN,  # Moderate restriction
        DefenseType.QUARANTINE,  # Most restrictive
    ]

    # Attack strategies (only used if defense is insufficient)
    # Ordered by intensity: lighter attacks first
    ATTACK_STRATEGIES = [
        AttackType.PORT_SCAN,  # Reconnaissance (lightest)
        AttackType.TRAFFIC_SHAPE,  # Bandwidth limiting
        AttackType.DNS_SPOOF,  # DNS redirection
        AttackType.DHCP_SPOOF,  # DHCP redirection
        AttackType.ICMP_REDIRECT,  # Route manipulation
        AttackType.BLOCK,  # ARP spoofing/ban
        AttackType.KICK,  # WiFi deauth/disassociate
        AttackType.MAC_FLOOD,  # Switch exhaustion
        AttackType.BEACON_FLOOD,  # WiFi confusion
    ]

    def __init__(
        self,
        state_manager: StateManager | None = None,
        qtable_persistence: QTablePersistence | None = None,
        telemetry_service: TelemetryService | None = None,
    ):
        """
        Initialize policy selector.

        Args:
            state_manager: StateManager instance (default: get_state_manager())
            qtable_persistence: QTablePersistence instance (default: new instance)
            telemetry_service: TelemetryService instance
                (default: get_telemetry_service())
        """
        self.state = state_manager or get_state_manager()
        self.qtable_persistence = qtable_persistence or QTablePersistence()
        self.qtable = self.qtable_persistence.load()
        self.cooldown = StrategyCooldown()
        self.backoff = StrategyBackoff()
        self.telemetry = telemetry_service or get_telemetry_service()

    def select_strategy_sequence(
        self, device: Device, max_strategies: int = 5
    ) -> list[StrategyIdentifier]:
        """
        Generate a defense-first strategy sequence for a device.

        Args:
            device: Target device
            max_strategies: Maximum number of strategies to return

        Returns:
            List of strategies ordered by priority (defense first)
        """
        device_features = self.state.get_device_state_features(device.mac)
        state_hash = self.qtable_persistence.compute_device_state_hash(device_features)

        # Score all available strategies
        scored_strategies = self._score_strategies(device, device_features, state_hash)

        # Filter out strategies on cooldown
        available = [
            s for s in scored_strategies if not self.cooldown.is_on_cooldown(s.strategy)
        ]

        # Sort by score (descending) and take top N
        available.sort(key=lambda x: x.score, reverse=True)
        selected = [s.strategy for s in available[:max_strategies]]

        logger.info(
            f"Selected {len(selected)} strategies for device {device.mac}: "
            f"{[s.strategy_id.value for s in selected]}"
        )

        return selected

    def _score_strategies(
        self, device: Device, device_features: dict[str, Any], state_hash: str
    ) -> list[StrategyScore]:
        """Score all available strategies for a device."""
        scores = []

        # Score defense strategies first (higher priority)
        for defense_type in self.DEFENSE_STRATEGIES:
            strategy = StrategyIdentifier(
                type=StrategyType.DEFENSE, strategy_id=defense_type
            )
            score = self._calculate_strategy_score(
                strategy, device, device_features, state_hash
            )
            scores.append(score)

        # Score attack strategies (lower priority)
        for attack_type in self.ATTACK_STRATEGIES:
            strategy = StrategyIdentifier(
                type=StrategyType.ATTACK, strategy_id=attack_type
            )
            score = self._calculate_strategy_score(
                strategy, device, device_features, state_hash
            )
            # Apply penalty to attack strategies (defense-first)
            score.score *= 0.5  # Reduce attack strategy scores by 50%
            scores.append(score)

        return scores

    def _calculate_strategy_score(
        self,
        strategy: StrategyIdentifier,
        device: Device,
        device_features: dict[str, Any],
        state_hash: str,
    ) -> StrategyScore:
        """
        Calculate score for a strategy using rule-based + RL approach.

        Score = (rule_score * 0.4) + (rl_score * 0.6)
        """
        # Rule-based score
        rule_score = self._rule_based_score(strategy, device, device_features)

        # RL-based score (from Q-table)
        q_entry = self.qtable.get_entry(state_hash, strategy)
        rl_score = q_entry.q_value if q_entry else 0.0

        # Apply backoff factor
        backoff = self.backoff.get_backoff_factor(strategy)
        rl_score *= backoff

        # Combine scores (weighted average)
        combined_score = (rule_score * 0.4) + (rl_score * 0.6)

        # Defense strategies get bonus
        if strategy.type == StrategyType.DEFENSE:
            combined_score *= 1.2  # 20% bonus
            combined_score = min(1.0, combined_score)  # Cap at 1.0

        return StrategyScore(
            strategy=strategy,
            score=combined_score,
            factors={
                "rule_score": rule_score,
                "rl_score": rl_score,
                "backoff": backoff,
                "defense_bonus": 1.2 if strategy.type == StrategyType.DEFENSE else 1.0,
            },
        )

    def _rule_based_score(
        self,
        strategy: StrategyIdentifier,
        device: Device,
        device_features: dict[str, Any],
    ) -> float:
        """
        Calculate rule-based score for a strategy.
        Returns score between 0.0 and 1.0.
        """
        score = 0.5  # Base score

        # Device type matching
        if device.type.value == "iot" and strategy.strategy_id in [
            DefenseType.UDP_RATE_LIMIT,
            DefenseType.TCP_RESET_POLICY,
        ]:
            score += 0.2  # IoT devices benefit from rate limiting

        # Device status matching
        if device.status.value == "blocked":
            # Already blocked, prefer stronger measures
            if strategy.strategy_id in [
                DefenseType.QUARANTINE,
                DefenseType.BLOCK_WAN,
            ]:
                score += 0.3

        # First seen device (new device)
        if device_features.get("is_first_seen", False):
            # New devices: prefer lighter defenses first
            if strategy.strategy_id in [
                DefenseType.WALLED_GARDEN,
                DefenseType.DNS_RPZ,
            ]:
                score += 0.2

        # Defense status
        if device.defense_status.value == "active":
            # Already has defense, prefer complementary strategies
            if strategy.strategy_id in [
                DefenseType.DNS_RPZ,
                DefenseType.TCP_RESET_POLICY,
            ]:
                score += 0.1

        # Attack type specific scoring
        if strategy.type == StrategyType.ATTACK:
            # Port scan is lightweight, good for reconnaissance
            if strategy.strategy_id == AttackType.PORT_SCAN:
                score += 0.1
            # Traffic shaping is less intrusive
            elif strategy.strategy_id == AttackType.TRAFFIC_SHAPE:
                score += 0.15
            # DNS/DHCP spoofing are moderate
            elif strategy.strategy_id in [AttackType.DNS_SPOOF, AttackType.DHCP_SPOOF]:
                score += 0.1
            # ICMP redirect is moderate
            elif strategy.strategy_id == AttackType.ICMP_REDIRECT:
                score += 0.1
            # MAC/Beacon flood are more aggressive
            elif strategy.strategy_id in [
                AttackType.MAC_FLOOD,
                AttackType.BEACON_FLOOD,
            ]:
                score -= 0.1  # Penalty for aggressive attacks

        return min(1.0, max(0.0, score))

    def update_strategy_score(
        self,
        device_mac: str,
        strategy: StrategyIdentifier,
        feedback: StrategyFeedback,
    ) -> None:
        """
        Update strategy score based on feedback (Q-learning update).

        Args:
            device_mac: Device MAC address
            strategy: Strategy that was applied
            feedback: Feedback on strategy effectiveness
        """
        # Store feedback in state manager
        self.state.add_strategy_feedback(feedback)

        # Get device state for Q-learning
        device = self.state.get_device(device_mac)
        if not device:
            logger.warning(f"Device {device_mac} not found for score update")
            return

        device_features = self.state.get_device_state_features(device_mac)
        state_hash = self.qtable_persistence.compute_device_state_hash(device_features)

        # Calculate reward from feedback
        # Reward = effect_score - resource_cost (normalized)
        reward = feedback.effect_score - (feedback.resource_cost * 0.5)

        # Get old Q-value for telemetry
        old_entry = self.qtable.get_entry(state_hash, strategy)
        old_q_value = old_entry.q_value if old_entry else None

        # Update Q-table
        # For simplicity, we don't have next state max Q, so we use reward directly
        new_entry = self.qtable.update_entry(state_hash, strategy, reward=reward)
        new_q_value = new_entry.q_value

        # Log score update
        self.telemetry.log_score_update(
            device_mac=device_mac,
            strategy=strategy,
            old_q_value=old_q_value,
            new_q_value=new_q_value,
            reward=reward,
        )

        # Update backoff based on effectiveness
        # Get old backoff factor before update
        old_backoff = self.backoff.get_backoff_factor(strategy)
        self.backoff.update_backoff(strategy, feedback.effect_score)
        new_backoff = self.backoff.get_backoff_factor(strategy)

        # Log backoff change if it changed
        if abs(new_backoff - old_backoff) > 0.001:
            self.telemetry.log_backoff(
                device_mac=device_mac,
                strategy=strategy,
                old_factor=old_backoff,
                new_factor=new_backoff,
                effect_score=feedback.effect_score,
            )

        # Set cooldown if strategy was ineffective
        if feedback.effect_score < 0.3:
            cooldown_duration = 300  # 5 minutes
            self.cooldown.set_cooldown(strategy, cooldown_duration)
            self.telemetry.log_cooldown(
                device_mac=device_mac,
                strategy=strategy,
                duration_seconds=cooldown_duration,
                reason="Low effectiveness",
            )
            logger.info(
                f"Strategy {strategy.strategy_id.value} on cooldown for "
                f"{cooldown_duration}s due to low effectiveness"
            )

        # Persist Q-table
        self.qtable_persistence.save(self.qtable)

        logger.info(
            f"Updated score for {strategy.strategy_id.value} on {device_mac}: "
            f"reward={reward:.2f}, effect={feedback.effect_score:.2f}"
        )


# Global accessor
def get_policy_selector() -> PolicySelector:
    """Get or create policy selector instance."""
    return PolicySelector()

    def get_best_strategy(self, device: Device) -> StrategyIdentifier | None:
        """
        Get the best strategy for a device (single strategy, not sequence).

        Returns:
            Best strategy or None if no strategies available
        """
        sequence = self.select_strategy_sequence(device, max_strategies=1)
        return sequence[0] if sequence else None

    async def auto_select_and_apply(
        self, device: Device, max_strategies: int = 3
    ) -> list[StrategyIdentifier]:
        """
        Automatically select and apply the best strategies for a device.
        This is the main entry point for AI-driven automatic defense.

        Args:
            device: Target device
            max_strategies: Maximum number of strategies to apply

        Returns:
            List of strategies that were selected and applied
        """
        logger.info(
            f"[PolicySelector] Auto-selecting strategies for device {device.mac}"
        )

        # Get strategy sequence
        strategies = self.select_strategy_sequence(
            device, max_strategies=max_strategies
        )

        if not strategies:
            logger.warning(
                f"[PolicySelector] No strategies available for device {device.mac}"
            )
            return []

        # Apply strategies (defense first, then attack if needed)
        applied = []
        for strategy in strategies:
            try:
                if strategy.type == StrategyType.DEFENSE:
                    # Apply defense policy
                    from app.models.defender import DefenseApplyRequest
                    from app.services.defender import (
                        get_defender_service,
                    )

                    defender = get_defender_service()
                    await defender.apply_defense(
                        device.mac, DefenseApplyRequest(policy=strategy.strategy_id)
                    )
                    applied.append(strategy)
                    logger.info(
                        f"[PolicySelector] Applied defense strategy "
                        f"{strategy.strategy_id.value} to device {device.mac}"
                    )

                elif strategy.type == StrategyType.ATTACK:
                    # Apply attack (with default duration)
                    from app.models.attack import AttackRequest
                    from app.services.attack import get_attack_service

                    attack_service = get_attack_service()
                    await attack_service.start_attack(
                        device.mac,
                        AttackRequest(
                            type=strategy.strategy_id,
                            duration=60,  # Default 60 seconds
                        ),
                    )
                    applied.append(strategy)
                    logger.info(
                        f"[PolicySelector] Applied attack strategy "
                        f"{strategy.strategy_id.value} to device {device.mac}"
                    )

                # Add small delay between strategies
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(
                    f"[PolicySelector] Failed to apply strategy "
                    f"{strategy.strategy_id.value} to device {device.mac}: {e}",
                    exc_info=True,
                )
                # Continue with next strategy even if one fails

        logger.info(
            f"[PolicySelector] Auto-applied {len(applied)} strategies "
            f"to device {device.mac}"
        )

        return applied
