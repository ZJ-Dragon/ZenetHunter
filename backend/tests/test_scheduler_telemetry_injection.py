"""Test to verify telemetry service dependency injection."""

import tempfile
from pathlib import Path

import pytest

from app.models.device import Device, DeviceStatus, DeviceType
from app.services.policy_selector import PolicySelector
from app.services.scheduler import SchedulerService
from app.services.state import StateManager
from app.services.telemetry import TelemetryService


def test_scheduler_telemetry_dependency_injection():
    """Test that SchedulerService passes telemetry_service to PolicySelector."""
    # Create a specific telemetry service instance
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test_telemetry.jsonl"
        telemetry = TelemetryService(log_file=log_file)

        # Create SchedulerService with the specific telemetry instance
        scheduler = SchedulerService(telemetry_service=telemetry)

        # Verify that SchedulerService uses the injected telemetry
        assert scheduler.telemetry is telemetry

        # Verify that PolicySelector also uses the same telemetry instance
        assert scheduler.selector.telemetry is telemetry
        assert scheduler.selector.telemetry is scheduler.telemetry


def test_scheduler_telemetry_with_explicit_policy_selector():
    """Test that explicit PolicySelector still works with telemetry injection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test_telemetry.jsonl"
        telemetry = TelemetryService(log_file=log_file)

        # Create PolicySelector with telemetry
        state = StateManager()
        policy_selector = PolicySelector(
            state_manager=state, telemetry_service=telemetry
        )

        # Create SchedulerService with explicit PolicySelector
        scheduler = SchedulerService(
            policy_selector=policy_selector, telemetry_service=telemetry
        )

        # Verify that the explicit PolicySelector is used
        assert scheduler.selector is policy_selector
        # Verify that both use the same telemetry instance
        assert scheduler.telemetry is telemetry
        assert scheduler.selector.telemetry is telemetry

