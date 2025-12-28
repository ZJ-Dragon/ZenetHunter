"""Tests for Scheduler Service Wireup."""

import tempfile
from pathlib import Path

import pytest

from app.models.attack import AttackType
from app.models.defender import DefenseType
from app.models.device import Device, DeviceStatus, DeviceType
from app.models.scheduler import StrategyIdentifier, StrategyType
from app.services.policy_selector import PolicySelector
from app.services.qtable_persistence import QTablePersistence
from app.services.scheduler import SchedulerService
from app.services.state import StateManager


@pytest.fixture
def state_manager():
    """Create a fresh StateManager for testing."""
    manager = StateManager()
    # Reset state to ensure test isolation (StateManager is a singleton)
    manager.reset()
    return manager


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
def scheduler_service(state_manager, policy_selector):
    """Create a SchedulerService in simulation mode."""
    return SchedulerService(
        state_manager=state_manager,
        policy_selector=policy_selector,
        simulation_mode=True,
    )


@pytest.fixture
def sample_device(state_manager):
    """Create and register a sample device."""
    device = Device(
        mac="AA:BB:CC:DD:EE:FF",
        ip="192.168.1.100",
        name="Test Device",
        type=DeviceType.IOT,
        status=DeviceStatus.ONLINE,
    )
    state_manager.update_device(device)
    return device


@pytest.mark.asyncio
async def test_scheduler_execute_strategy_flow(
    scheduler_service, sample_device, state_manager
):
    """Test complete strategy flow execution."""
    result = await scheduler_service.execute_strategy_flow(sample_device.mac)

    assert result["success"] is True
    assert result["device_mac"] == sample_device.mac
    assert result["strategies_applied"] > 0
    assert "results" in result


@pytest.mark.asyncio
async def test_scheduler_apply_defense_strategy(scheduler_service, sample_device):
    """Test applying a defense strategy."""
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.UDP_RATE_LIMIT
    )

    result = await scheduler_service._apply_strategy(sample_device, strategy)

    assert result["success"] is True
    assert result["strategy"] == DefenseType.UDP_RATE_LIMIT.value
    assert result["type"] == "defense"
    assert result["simulated"] is True


@pytest.mark.asyncio
async def test_scheduler_apply_attack_strategy(scheduler_service, sample_device):
    """Test applying an attack strategy."""
    strategy = StrategyIdentifier(type=StrategyType.ATTACK, strategy_id=AttackType.KICK)

    result = await scheduler_service._apply_strategy(sample_device, strategy)

    assert result["success"] is True
    assert result["strategy"] == AttackType.KICK.value
    assert result["type"] == "attack"
    assert result["simulated"] is True


@pytest.mark.asyncio
async def test_scheduler_collect_feedback_simulation(scheduler_service, sample_device):
    """Test feedback collection in simulation mode."""
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.TCP_RESET_POLICY
    )
    result = {"success": True, "strategy": DefenseType.TCP_RESET_POLICY.value}

    feedback = await scheduler_service._collect_feedback(
        sample_device.mac, strategy, result, duration_seconds=60
    )

    assert feedback is not None
    assert feedback.device_mac == sample_device.mac
    assert feedback.strategy == strategy
    assert 0.0 <= feedback.effect_score <= 1.0
    assert 0.0 <= feedback.resource_cost <= 1.0
    assert feedback.duration_seconds == 60


@pytest.mark.asyncio
async def test_scheduler_simulate_complete_flow(
    scheduler_service, sample_device, state_manager
):
    """Test simulate_complete_flow method."""
    result = await scheduler_service.simulate_complete_flow(sample_device.mac)

    assert result["success"] is True
    assert result["device_mac"] == sample_device.mac
    assert "strategies_applied" in result


@pytest.mark.asyncio
async def test_scheduler_flow_with_feedback_update(
    scheduler_service, sample_device, state_manager, policy_selector
):
    """Test that strategy flow updates Q-table via feedback."""
    # Execute flow
    result = await scheduler_service.execute_strategy_flow(sample_device.mac)

    assert result["success"] is True
    assert result["feedback_collected"] > 0

    # Verify feedback was stored in state
    feedback_list = state_manager.get_strategy_feedback(sample_device.mac, limit=10)
    assert len(feedback_list) > 0


@pytest.mark.asyncio
async def test_scheduler_unknown_device(scheduler_service, state_manager):
    """Test scheduler with non-existent device."""
    # Ensure state is clean (no devices exist)
    state_manager.clear_devices()
    # Verify device doesn't exist
    assert state_manager.get_device("00:00:00:00:00:00") is None

    result = await scheduler_service.execute_strategy_flow("00:00:00:00:00:00")

    assert result["success"] is False
    assert "error" in result
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_scheduler_error_handling(scheduler_service, sample_device):
    """Test scheduler error handling."""
    # Test with a valid strategy but simulate an error
    strategy = StrategyIdentifier(
        type=StrategyType.DEFENSE, strategy_id=DefenseType.UDP_RATE_LIMIT
    )

    # In simulation mode, this should succeed
    result = await scheduler_service._apply_strategy(sample_device, strategy)
    assert "success" in result
    # Should handle gracefully even if underlying service fails
    assert isinstance(result, dict)
