"""Tests for Telemetry Service."""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.models.attack import AttackType
from app.models.defender import DefenseType
from app.models.scheduler import StrategyFeedback, StrategyIdentifier, StrategyType
from app.services.telemetry import (
    TelemetryEvent,
    TelemetryEventType,
    TelemetryService,
)


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "telemetry.jsonl"
        yield log_file


@pytest.fixture
def telemetry_service(temp_log_file):
    """Create a TelemetryService instance with temp file."""
    return TelemetryService(log_file=temp_log_file)


def test_telemetry_log_event(telemetry_service, temp_log_file):
    """Test logging a telemetry event."""
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.UDP_RATE_LIMIT
    )
    event = TelemetryEvent(
        event_type=TelemetryEventType.STRATEGY_SWITCH,
        device_mac="AA:BB:CC:DD:EE:FF",
        strategy=strategy,
        metrics={"test": "value"},
    )

    telemetry_service.log_event(event)

    # Verify file was created and contains the event
    assert temp_log_file.exists()
    import json

    with open(temp_log_file) as f:
        lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0].strip())
        assert data["event_type"] == "strategy_switch"


def test_telemetry_log_strategy_switch(telemetry_service, temp_log_file):
    """Test logging strategy switch."""
    from_strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.UDP_RATE_LIMIT
    )
    to_strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.TCP_RESET_POLICY
    )

    telemetry_service.log_strategy_switch(
        device_mac="AA:BB:CC:DD:EE:FF",
        from_strategy=from_strategy,
        to_strategy=to_strategy,
        reason="Policy update",
    )

    # Verify event was logged
    events = telemetry_service.search_events(
        event_type=TelemetryEventType.STRATEGY_SWITCH
    )
    assert len(events) == 1
    assert events[0].device_mac == "AA:BB:CC:DD:EE:FF"
    assert events[0].metrics["to_strategy"] == DefenseType.TCP_RESET_POLICY.value


def test_telemetry_log_backoff(telemetry_service):
    """Test logging backoff event."""
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.WALLED_GARDEN
    )

    telemetry_service.log_backoff(
        device_mac="AA:BB:CC:DD:EE:FF",
        strategy=strategy,
        old_factor=1.0,
        new_factor=0.9,
        effect_score=0.2,
    )

    events = telemetry_service.search_events(event_type=TelemetryEventType.BACKOFF)
    assert len(events) == 1
    assert events[0].metrics["old_backoff_factor"] == 1.0
    assert events[0].metrics["new_backoff_factor"] == 0.9
    assert events[0].metrics["effect_score"] == 0.2


def test_telemetry_log_cooldown(telemetry_service):
    """Test logging cooldown event."""
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.DNS_RPZ
    )

    telemetry_service.log_cooldown(
        device_mac="AA:BB:CC:DD:EE:FF",
        strategy=strategy,
        duration_seconds=300,
        reason="Low effectiveness",
    )

    events = telemetry_service.search_events(event_type=TelemetryEventType.COOLDOWN)
    assert len(events) == 1
    assert events[0].metrics["duration_seconds"] == 300
    assert events[0].metrics["reason"] == "Low effectiveness"


def test_telemetry_log_effectiveness(telemetry_service):
    """Test logging effectiveness metrics."""
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.TCP_RESET_POLICY
    )
    feedback = StrategyFeedback(
        device_mac="AA:BB:CC:DD:EE:FF",
        strategy=strategy,
        effect_score=0.7,
        resource_cost=0.3,
        duration_seconds=60,
        device_response="disconnected",
    )

    telemetry_service.log_effectiveness("AA:BB:CC:DD:EE:FF", strategy, feedback)

    events = telemetry_service.search_events(
        event_type=TelemetryEventType.EFFECTIVENESS
    )
    assert len(events) == 1
    assert events[0].metrics["effect_score"] == 0.7
    assert events[0].metrics["resource_cost"] == 0.3


def test_telemetry_log_score_update(telemetry_service):
    """Test logging score update."""
    strategy = StrategyIdentifier(type=StrategyType.ATTACK, strategy_id=AttackType.KICK)

    telemetry_service.log_score_update(
        device_mac="AA:BB:CC:DD:EE:FF",
        strategy=strategy,
        old_q_value=0.5,
        new_q_value=0.6,
        reward=0.3,
    )

    events = telemetry_service.search_events(event_type=TelemetryEventType.SCORE_UPDATE)
    assert len(events) == 1
    assert events[0].metrics["old_q_value"] == 0.5
    assert events[0].metrics["new_q_value"] == 0.6
    assert events[0].metrics["reward"] == 0.3


def test_telemetry_search_by_device(telemetry_service):
    """Test searching events by device MAC."""
    strategy1 = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.UDP_RATE_LIMIT
    )
    strategy2 = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.TCP_RESET_POLICY
    )

    # Log events for different devices
    telemetry_service.log_strategy_switch(
        device_mac="AA:BB:CC:DD:EE:FF", from_strategy=None, to_strategy=strategy1
    )
    telemetry_service.log_strategy_switch(
        device_mac="11:22:33:44:55:66", from_strategy=None, to_strategy=strategy2
    )

    # Search for specific device
    events = telemetry_service.search_events(device_mac="AA:BB:CC:DD:EE:FF")
    assert len(events) == 1
    assert events[0].device_mac == "AA:BB:CC:DD:EE:FF"


def test_telemetry_search_by_strategy(telemetry_service):
    """Test searching events by strategy ID."""
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.UDP_RATE_LIMIT
    )

    telemetry_service.log_strategy_switch(
        device_mac="AA:BB:CC:DD:EE:FF", from_strategy=None, to_strategy=strategy
    )

    events = telemetry_service.search_events(
        strategy_id=DefenseType.UDP_RATE_LIMIT.value
    )
    assert len(events) == 1
    assert events[0].strategy.strategy_id == DefenseType.UDP_RATE_LIMIT


def test_telemetry_search_by_time_range(telemetry_service):
    """Test searching events by time range."""
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.UDP_RATE_LIMIT
    )

    # Log event now
    telemetry_service.log_strategy_switch(
        device_mac="AA:BB:CC:DD:EE:FF", from_strategy=None, to_strategy=strategy
    )

    # Search with time range
    start_time = datetime.now(UTC) - timedelta(hours=1)
    end_time = datetime.now(UTC) + timedelta(hours=1)

    events = telemetry_service.search_events(start_time=start_time, end_time=end_time)
    assert len(events) == 1

    # Search outside time range
    future_start = datetime.now(UTC) + timedelta(hours=1)
    events = telemetry_service.search_events(start_time=future_start)
    assert len(events) == 0


def test_telemetry_get_backoff_history(telemetry_service):
    """Test getting backoff history for a strategy."""
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.UDP_RATE_LIMIT
    )

    # Log multiple backoff events
    telemetry_service.log_backoff(
        device_mac="AA:BB:CC:DD:EE:FF",
        strategy=strategy,
        old_factor=1.0,
        new_factor=0.9,
        effect_score=0.2,
    )
    telemetry_service.log_backoff(
        device_mac="AA:BB:CC:DD:EE:FF",
        strategy=strategy,
        old_factor=0.9,
        new_factor=0.8,
        effect_score=0.1,
    )

    history = telemetry_service.get_backoff_history(strategy)
    assert len(history) == 2
    # Should be sorted by timestamp (newest first)
    assert history[0].timestamp >= history[1].timestamp


def test_telemetry_get_strategy_switches(telemetry_service):
    """Test getting strategy switch history."""
    strategy1 = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.UDP_RATE_LIMIT
    )
    strategy2 = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.TCP_RESET_POLICY
    )

    telemetry_service.log_strategy_switch(
        device_mac="AA:BB:CC:DD:EE:FF", from_strategy=None, to_strategy=strategy1
    )
    telemetry_service.log_strategy_switch(
        device_mac="AA:BB:CC:DD:EE:FF",
        from_strategy=strategy1,
        to_strategy=strategy2,
    )

    switches = telemetry_service.get_strategy_switches(device_mac="AA:BB:CC:DD:EE:FF")
    assert len(switches) == 2
