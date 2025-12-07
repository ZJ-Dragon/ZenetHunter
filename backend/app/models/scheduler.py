"""AI Scheduler Schema: Strategy Scoring and Q-Table Models."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.attack import AttackType
from app.models.defender import DefenseType


class StrategyType(str, Enum):
    """Type of strategy (defense or attack)."""

    DEFENSE = "defense"
    ATTACK = "attack"


class StrategyIdentifier(BaseModel):
    """Unified identifier for a strategy (defense or attack)."""

    type: StrategyType = Field(..., description="Strategy type")
    strategy_id: DefenseType | AttackType = Field(
        ..., description="Specific strategy identifier"
    )

    model_config = ConfigDict(from_attributes=True)


class StrategyScore(BaseModel):
    """Score for a strategy based on multiple factors."""

    strategy: StrategyIdentifier = Field(..., description="Strategy identifier")
    score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall score (0.0-1.0)"
    )
    factors: dict[str, float] = Field(
        default_factory=dict,
        description="Individual factor scores (e.g., feature_match, resource_cost)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When this score was calculated",
    )

    model_config = ConfigDict(from_attributes=True)


class StrategyFeedback(BaseModel):
    """Feedback on strategy effectiveness after execution."""

    device_mac: str = Field(..., description="Target device MAC")
    strategy: StrategyIdentifier = Field(..., description="Strategy that was applied")
    effect_score: float = Field(
        ..., ge=0.0, le=1.0, description="Effectiveness (0.0=no effect, 1.0=highly effective)"
    )
    resource_cost: float = Field(
        ..., ge=0.0, le=1.0, description="Resource consumption (0.0=low, 1.0=high)"
    )
    duration_seconds: int = Field(
        ..., ge=0, description="How long the strategy was active"
    )
    device_response: str | None = Field(
        None, description="Observed device response (e.g., 'disconnected', 'still_active')"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When feedback was recorded",
    )

    model_config = ConfigDict(from_attributes=True)


class QEntry(BaseModel):
    """Q-Table entry for a state-action pair."""

    device_state_hash: str = Field(
        ..., description="Hash of device state (MAC + features)"
    )
    strategy: StrategyIdentifier = Field(..., description="Strategy identifier")
    q_value: float = Field(
        default=0.0, description="Q-value (expected future reward)"
    )
    visit_count: int = Field(default=0, ge=0, description="Number of times tried")
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last time this entry was updated",
    )

    model_config = ConfigDict(from_attributes=True)


class QTable(BaseModel):
    """Q-Table for reinforcement learning."""

    entries: dict[str, QEntry] = Field(
        default_factory=dict,
        description="Q-entries keyed by state-action hash",
    )
    learning_rate: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Q-learning learning rate (alpha)"
    )
    discount_factor: float = Field(
        default=0.9, ge=0.0, le=1.0, description="Q-learning discount factor (gamma)"
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last time Q-table was updated",
    )

    model_config = ConfigDict(from_attributes=True)

    def get_entry(
        self, device_state_hash: str, strategy: StrategyIdentifier
    ) -> QEntry | None:
        """Get Q-entry for a state-action pair."""
        key = self._make_key(device_state_hash, strategy)
        return self.entries.get(key)

    def update_entry(
        self,
        device_state_hash: str,
        strategy: StrategyIdentifier,
        reward: float,
        next_max_q: float | None = None,
    ) -> QEntry:
        """Update Q-entry using Q-learning formula."""
        key = self._make_key(device_state_hash, strategy)
        entry = self.entries.get(key)

        if entry is None:
            entry = QEntry(
                device_state_hash=device_state_hash,
                strategy=strategy,
                q_value=0.0,
            )
            self.entries[key] = entry

        # Q-learning update: Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
        if next_max_q is not None:
            td_target = reward + (self.discount_factor * next_max_q)
        else:
            td_target = reward

        td_error = td_target - entry.q_value
        entry.q_value += self.learning_rate * td_error
        entry.visit_count += 1
        entry.last_updated = datetime.now(UTC)
        self.last_updated = datetime.now(UTC)

        return entry

    def _make_key(self, device_state_hash: str, strategy: StrategyIdentifier) -> str:
        """Generate a unique key for state-action pair."""
        return f"{device_state_hash}:{strategy.type.value}:{strategy.strategy_id.value}"

