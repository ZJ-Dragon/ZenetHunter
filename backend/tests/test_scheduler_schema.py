"""Tests for AI Scheduler Schema and Persistence."""

import json
import tempfile
from pathlib import Path

import pytest

from app.models.attack import AttackType
from app.models.defender import DefenseType
from app.models.scheduler import (
    QEntry,
    QTable,
    StrategyFeedback,
    StrategyIdentifier,
    StrategyScore,
    StrategyType,
)
from app.services.qtable_persistence import QTablePersistence


def test_strategy_identifier():
    """Test StrategyIdentifier model."""
    # Defense strategy
    defense_id = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.UDP_RATE_LIMIT
    )
    assert defense_id.type == StrategyType.DEFENSE
    assert defense_id.strategy_id == DefenseType.UDP_RATE_LIMIT

    # Attack strategy
    attack_id = StrategyIdentifier(
        type=StrategyType.ATTACK, strategy_id=AttackType.KICK
    )
    assert attack_id.type == StrategyType.ATTACK
    assert attack_id.strategy_id == AttackType.KICK


def test_strategy_score():
    """Test StrategyScore model."""
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.TCP_RESET_POLICY
    )
    score = StrategyScore(
        strategy=strategy,
        score=0.85,
        factors={"feature_match": 0.9, "resource_cost": 0.2},
    )
    assert score.score == 0.85
    assert score.factors["feature_match"] == 0.9
    assert score.factors["resource_cost"] == 0.2


def test_strategy_feedback():
    """Test StrategyFeedback model."""
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.WALLED_GARDEN
    )
    feedback = StrategyFeedback(
        device_mac="AA:BB:CC:DD:EE:FF",
        strategy=strategy,
        effect_score=0.7,
        resource_cost=0.3,
        duration_seconds=300,
        device_response="disconnected",
    )
    assert feedback.device_mac == "AA:BB:CC:DD:EE:FF"
    assert feedback.effect_score == 0.7
    assert feedback.resource_cost == 0.3
    assert feedback.duration_seconds == 300


def test_q_entry():
    """Test QEntry model."""
    strategy = StrategyIdentifier(
        type=StrategyType.ATTACK, strategy_id=AttackType.BLOCK
    )
    entry = QEntry(
        device_state_hash="abc123",
        strategy=strategy,
        q_value=0.5,
        visit_count=10,
    )
    assert entry.device_state_hash == "abc123"
    assert entry.q_value == 0.5
    assert entry.visit_count == 10


def test_q_table_operations():
    """Test QTable operations."""
    qtable = QTable(learning_rate=0.1, discount_factor=0.9)

    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.UDP_RATE_LIMIT
    )
    state_hash = "test_state_123"

    # Get non-existent entry
    entry = qtable.get_entry(state_hash, strategy)
    assert entry is None

    # Update entry (first time, no next state)
    entry = qtable.update_entry(state_hash, strategy, reward=0.5)
    # Q(s,a) = Q(s,a) + α[r - Q(s,a)] = 0 + 0.1 * [0.5 - 0] = 0.05
    assert entry.q_value == pytest.approx(0.05, abs=0.001)
    assert entry.visit_count == 1

    # Update entry (Q-learning with next state)
    entry = qtable.update_entry(
        state_hash, strategy, reward=0.3, next_max_q=0.8
    )
    # Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
    # Q = 0.05 + 0.1 * [0.3 + 0.9*0.8 - 0.05] = 0.05 + 0.1 * 0.97 = 0.147
    assert entry.q_value == pytest.approx(0.147, abs=0.001)
    assert entry.visit_count == 2

    # Get entry
    retrieved = qtable.get_entry(state_hash, strategy)
    assert retrieved is not None
    assert retrieved.q_value == pytest.approx(0.147, abs=0.001)


def test_qtable_persistence_save_load():
    """Test Q-table persistence save and load."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "qtable.json"
        persistence = QTablePersistence(storage_path=storage_path)

        # Create and populate Q-table
        qtable = QTable(learning_rate=0.1, discount_factor=0.9)
        strategy = StrategyIdentifier(
            type=StrategyType.DEFENSE, strategy_id=DefenseType.TCP_RESET_POLICY
        )
        qtable.update_entry("state1", strategy, reward=0.8)

        # Save
        persistence.save(qtable)

        # Load
        loaded = persistence.load()
        assert loaded.learning_rate == 0.1
        assert loaded.discount_factor == 0.9
        assert len(loaded.entries) == 1

        # Verify entry
        entry = loaded.get_entry("state1", strategy)
        assert entry is not None
        # Q = 0 + 0.1 * [0.8 - 0] = 0.08
        assert entry.q_value == pytest.approx(0.08, abs=0.001)


def test_qtable_persistence_device_state_hash():
    """Test device state hash computation."""
    persistence = QTablePersistence()

    device_data1 = {"mac": "AA:BB:CC:DD:EE:FF", "type": "mobile"}
    device_data2 = {"mac": "AA:BB:CC:DD:EE:FF", "type": "mobile"}
    device_data3 = {"mac": "AA:BB:CC:DD:EE:FF", "type": "pc"}

    hash1 = persistence.compute_device_state_hash(device_data1)
    hash2 = persistence.compute_device_state_hash(device_data2)
    hash3 = persistence.compute_device_state_hash(device_data3)

    # Same data should produce same hash
    assert hash1 == hash2
    # Different data should produce different hash
    assert hash1 != hash3

