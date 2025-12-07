"""Tests for Policy Selector Service."""

import tempfile
from pathlib import Path

import pytest

from app.models.defender import DefenseType
from app.models.device import Device, DeviceStatus, DeviceType
from app.models.scheduler import StrategyFeedback, StrategyIdentifier, StrategyType
from app.services.policy_selector import (
    PolicySelector,
    StrategyBackoff,
    StrategyCooldown,
)
from app.services.qtable_persistence import QTablePersistence
from app.services.state import StateManager


@pytest.fixture
def state_manager():
    """Create a fresh StateManager for testing."""
    return StateManager()


@pytest.fixture
def qtable_persistence():
    """Create a temporary Q-table persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "qtable.json"
        yield QTablePersistence(storage_path=storage_path)


@pytest.fixture
def policy_selector(state_manager, qtable_persistence):
    """Create a PolicySelector instance."""
    return PolicySelector(
        state_manager=state_manager, qtable_persistence=qtable_persistence
    )


@pytest.fixture
def sample_device():
    """Create a sample device for testing."""
    return Device(
        mac="AA:BB:CC:DD:EE:FF",
        ip="192.168.1.100",
        name="Test Device",
        type=DeviceType.IOT,
        status=DeviceStatus.ONLINE,
    )


def test_strategy_cooldown():
    """Test StrategyCooldown functionality."""
    cooldown = StrategyCooldown()
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.UDP_RATE_LIMIT
    )

    # Not on cooldown initially
    assert not cooldown.is_on_cooldown(strategy)
    assert cooldown.get_remaining_cooldown(strategy) is None

    # Set cooldown
    cooldown.set_cooldown(strategy, duration_seconds=60)
    assert cooldown.is_on_cooldown(strategy)
    remaining = cooldown.get_remaining_cooldown(strategy)
    assert remaining is not None
    assert 0 < remaining <= 60


def test_strategy_backoff():
    """Test StrategyBackoff functionality."""
    backoff = StrategyBackoff()
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.TCP_RESET_POLICY
    )

    # Initial backoff factor is 1.0
    assert backoff.get_backoff_factor(strategy) == 1.0

    # Update with low effectiveness -> backoff increases
    backoff.update_backoff(strategy, effect_score=0.2)
    factor = backoff.get_backoff_factor(strategy)
    assert factor < 1.0  # Backoff reduced

    # Update with high effectiveness -> backoff decreases
    backoff.update_backoff(strategy, effect_score=0.8)
    factor = backoff.get_backoff_factor(strategy)
    assert factor > 0.0  # Backoff increased (but capped at 1.0)


def test_policy_selector_defense_first(policy_selector, sample_device):
    """Test that defense strategies are prioritized."""
    sequence = policy_selector.select_strategy_sequence(sample_device, max_strategies=5)

    # Should return strategies
    assert len(sequence) > 0

    # First strategy should be defense
    assert sequence[0].type == StrategyType.DEFENSE

    # Count defense vs attack strategies
    defense_count = sum(1 for s in sequence if s.type == StrategyType.DEFENSE)
    attack_count = sum(1 for s in sequence if s.type == StrategyType.ATTACK)

    # Defense should be prioritized
    assert defense_count >= attack_count


def test_policy_selector_rule_based_scoring(
    policy_selector, sample_device, state_manager
):
    """Test rule-based scoring logic."""
    # Add device to state
    state_manager.update_device(sample_device)

    # Get device features
    features = state_manager.get_device_state_features(sample_device.mac)

    # Score a strategy
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.UDP_RATE_LIMIT
    )
    score = policy_selector._rule_based_score(strategy, sample_device, features)

    # Score should be between 0.0 and 1.0
    assert 0.0 <= score <= 1.0


def test_policy_selector_strategy_sequence(
    policy_selector, sample_device, state_manager
):
    """Test strategy sequence generation."""
    # Add device to state
    state_manager.update_device(sample_device)

    # Generate sequence
    sequence = policy_selector.select_strategy_sequence(sample_device, max_strategies=3)

    # Should return strategies
    assert len(sequence) > 0
    assert len(sequence) <= 3

    # All should be StrategyIdentifier instances
    for s in sequence:
        assert isinstance(s, StrategyIdentifier)


def test_policy_selector_cooldown_filtering(
    policy_selector, sample_device, state_manager
):
    """Test that strategies on cooldown are filtered out."""
    # Add device to state
    state_manager.update_device(sample_device)

    # Set a strategy on cooldown
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.UDP_RATE_LIMIT
    )
    policy_selector.cooldown.set_cooldown(strategy, duration_seconds=300)

    # Generate sequence
    sequence = policy_selector.select_strategy_sequence(
        sample_device, max_strategies=10
    )

    # Cooldown strategy should not be in sequence
    assert strategy not in sequence


def test_policy_selector_score_update(
    policy_selector, sample_device, state_manager, qtable_persistence
):
    """Test strategy score update with feedback."""
    # Add device to state
    state_manager.update_device(sample_device)

    # Create feedback
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.TCP_RESET_POLICY
    )
    feedback = StrategyFeedback(
        device_mac=sample_device.mac,
        strategy=strategy,
        effect_score=0.7,
        resource_cost=0.2,
        duration_seconds=60,
        device_response="disconnected",
    )

    # Update score
    policy_selector.update_strategy_score(sample_device.mac, strategy, feedback)

    # Verify feedback was stored
    stored_feedback = state_manager.get_strategy_feedback(sample_device.mac, limit=1)
    assert len(stored_feedback) > 0
    assert stored_feedback[0].effect_score == 0.7

    # Verify Q-table was updated
    device_features = state_manager.get_device_state_features(sample_device.mac)
    state_hash = qtable_persistence.compute_device_state_hash(device_features)
    q_entry = policy_selector.qtable.get_entry(state_hash, strategy)
    assert q_entry is not None
    assert q_entry.visit_count > 0


def test_policy_selector_low_effectiveness_cooldown(
    policy_selector, sample_device, state_manager
):
    """Test that low effectiveness triggers cooldown."""
    # Add device to state
    state_manager.update_device(sample_device)

    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.WALLED_GARDEN
    )

    # Create feedback with low effectiveness
    feedback = StrategyFeedback(
        device_mac=sample_device.mac,
        strategy=strategy,
        effect_score=0.2,  # Low effectiveness
        resource_cost=0.5,
        duration_seconds=60,
    )

    # Update score
    policy_selector.update_strategy_score(sample_device.mac, strategy, feedback)

    # Strategy should be on cooldown
    assert policy_selector.cooldown.is_on_cooldown(strategy)


def test_policy_selector_get_best_strategy(
    policy_selector, sample_device, state_manager
):
    """Test getting the best single strategy."""
    # Add device to state
    state_manager.update_device(sample_device)

    # Get best strategy
    best = policy_selector.get_best_strategy(sample_device)

    # Should return a strategy
    assert best is not None
    assert isinstance(best, StrategyIdentifier)
    # Should be defense (defense-first)
    assert best.type == StrategyType.DEFENSE
