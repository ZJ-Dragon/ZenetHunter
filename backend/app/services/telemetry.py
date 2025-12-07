"""Telemetry Service: Structured JSON logging for scheduler events and metrics."""

import json
import logging
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.scheduler import StrategyFeedback, StrategyIdentifier

logger = logging.getLogger(__name__)


class TelemetryEventType(str, Enum):
    """Types of telemetry events."""

    STRATEGY_SWITCH = "strategy_switch"
    BACKOFF = "backoff"
    COOLDOWN = "cooldown"
    EFFECTIVENESS = "effectiveness"
    SCORE_UPDATE = "score_update"
    STRATEGY_APPLIED = "strategy_applied"
    STRATEGY_FAILED = "strategy_failed"


class TelemetryEvent(BaseModel):
    """Structured telemetry event."""

    event_type: TelemetryEventType = Field(..., description="Event type")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Event timestamp"
    )
    device_mac: str | None = Field(None, description="Target device MAC")
    strategy: StrategyIdentifier | None = Field(None, description="Strategy involved")
    metrics: dict[str, Any] = Field(
        default_factory=dict, description="Event-specific metrics"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )

    model_config = ConfigDict(from_attributes=True)

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.model_dump(mode="json"), ensure_ascii=False, indent=2)


class TelemetryService:
    """
    Telemetry service for logging scheduler events and metrics.
    Logs structured JSON events for retrieval and analysis.
    """

    def __init__(self, log_file: Path | str | None = None):
        """
        Initialize telemetry service.

        Args:
            log_file: Path to telemetry log file. Defaults to ./data/telemetry.jsonl
        """
        if log_file is None:
            log_file = Path("./data/telemetry.jsonl")
        elif isinstance(log_file, str):
            log_file = Path(log_file)

        self.log_file = log_file
        # Ensure directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event: TelemetryEvent) -> None:
        """
        Log a telemetry event to file (JSONL format).

        Args:
            event: Telemetry event to log
        """
        try:
            # Append to JSONL file (one JSON object per line)
            with open(self.log_file, "a") as f:
                json_line = json.dumps(
                    event.model_dump(mode="json"), ensure_ascii=False
                )
                f.write(json_line + "\n")

            # Also log via standard logger
            logger.info(
                f"[Telemetry] {event.event_type.value}: "
                f"device={event.device_mac}, strategy={event.strategy.strategy_id.value if event.strategy else None}"
            )
        except Exception as e:
            logger.error(f"Failed to log telemetry event: {e}")

    def log_strategy_switch(
        self,
        device_mac: str,
        from_strategy: StrategyIdentifier | None,
        to_strategy: StrategyIdentifier,
        reason: str | None = None,
    ) -> None:
        """Log a strategy switch event."""
        event = TelemetryEvent(
            event_type=TelemetryEventType.STRATEGY_SWITCH,
            device_mac=device_mac,
            strategy=to_strategy,
            metrics={
                "from_strategy": (
                    from_strategy.strategy_id.value if from_strategy else None
                ),
                "to_strategy": to_strategy.strategy_id.value,
                "reason": reason,
            },
        )
        self.log_event(event)

    def log_backoff(
        self,
        device_mac: str | None,
        strategy: StrategyIdentifier,
        old_factor: float,
        new_factor: float,
        effect_score: float,
    ) -> None:
        """Log a backoff event."""
        event = TelemetryEvent(
            event_type=TelemetryEventType.BACKOFF,
            device_mac=device_mac,
            strategy=strategy,
            metrics={
                "old_backoff_factor": old_factor,
                "new_backoff_factor": new_factor,
                "effect_score": effect_score,
                "backoff_change": new_factor - old_factor,
            },
        )
        self.log_event(event)

    def log_cooldown(
        self,
        device_mac: str | None,
        strategy: StrategyIdentifier,
        duration_seconds: int,
        reason: str | None = None,
    ) -> None:
        """Log a cooldown event."""
        event = TelemetryEvent(
            event_type=TelemetryEventType.COOLDOWN,
            device_mac=device_mac,
            strategy=strategy,
            metrics={
                "duration_seconds": duration_seconds,
                "reason": reason,
            },
        )
        self.log_event(event)

    def log_effectiveness(
        self,
        device_mac: str,
        strategy: StrategyIdentifier,
        feedback: StrategyFeedback,
    ) -> None:
        """Log effectiveness metrics."""
        event = TelemetryEvent(
            event_type=TelemetryEventType.EFFECTIVENESS,
            device_mac=device_mac,
            strategy=strategy,
            metrics={
                "effect_score": feedback.effect_score,
                "resource_cost": feedback.resource_cost,
                "duration_seconds": feedback.duration_seconds,
                "device_response": feedback.device_response,
            },
        )
        self.log_event(event)

    def log_score_update(
        self,
        device_mac: str,
        strategy: StrategyIdentifier,
        old_q_value: float | None,
        new_q_value: float,
        reward: float,
    ) -> None:
        """Log a Q-table score update."""
        event = TelemetryEvent(
            event_type=TelemetryEventType.SCORE_UPDATE,
            device_mac=device_mac,
            strategy=strategy,
            metrics={
                "old_q_value": old_q_value,
                "new_q_value": new_q_value,
                "reward": reward,
                "q_value_change": new_q_value - (old_q_value or 0.0),
            },
        )
        self.log_event(event)

    def log_strategy_applied(
        self,
        device_mac: str,
        strategy: StrategyIdentifier,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Log strategy application result."""
        event_type = (
            TelemetryEventType.STRATEGY_APPLIED
            if success
            else TelemetryEventType.STRATEGY_FAILED
        )
        event = TelemetryEvent(
            event_type=event_type,
            device_mac=device_mac,
            strategy=strategy,
            metrics={
                "success": success,
                "error": error,
            },
        )
        self.log_event(event)

    def search_events(
        self,
        event_type: TelemetryEventType | None = None,
        device_mac: str | None = None,
        strategy_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[TelemetryEvent]:
        """
        Search telemetry events by criteria.

        Args:
            event_type: Filter by event type
            device_mac: Filter by device MAC
            strategy_id: Filter by strategy ID
            start_time: Filter events after this time
            end_time: Filter events before this time
            limit: Maximum number of events to return

        Returns:
            List of matching telemetry events
        """
        if not self.log_file.exists():
            return []

        events = []
        try:
            with open(self.log_file) as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        event = TelemetryEvent(**data)

                        # Apply filters
                        if event_type and event.event_type != event_type:
                            continue
                        if device_mac and event.device_mac != device_mac:
                            continue
                        if strategy_id and (
                            not event.strategy
                            or event.strategy.strategy_id.value != strategy_id
                        ):
                            continue
                        if start_time and event.timestamp < start_time:
                            continue
                        if end_time and event.timestamp > end_time:
                            continue

                        events.append(event)
                    except Exception as e:
                        logger.warning(f"Failed to parse telemetry event: {e}")
                        continue

            # Sort by timestamp (newest first) and limit
            events.sort(key=lambda x: x.timestamp, reverse=True)
            return events[:limit]

        except Exception as e:
            logger.error(f"Failed to search telemetry events: {e}")
            return []

    def get_backoff_history(
        self, strategy: StrategyIdentifier, limit: int = 50
    ) -> list[TelemetryEvent]:
        """Get backoff history for a strategy."""
        return self.search_events(
            event_type=TelemetryEventType.BACKOFF,
            strategy_id=strategy.strategy_id.value,
            limit=limit,
        )

    def get_strategy_switches(
        self, device_mac: str | None = None, limit: int = 50
    ) -> list[TelemetryEvent]:
        """Get strategy switch history."""
        return self.search_events(
            event_type=TelemetryEventType.STRATEGY_SWITCH,
            device_mac=device_mac,
            limit=limit,
        )


# Global instance
_telemetry_instance: TelemetryService | None = None


def get_telemetry_service() -> TelemetryService:
    """Get global TelemetryService instance."""
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = TelemetryService()
    return _telemetry_instance
