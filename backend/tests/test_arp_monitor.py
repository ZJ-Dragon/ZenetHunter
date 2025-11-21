import asyncio
from unittest.mock import patch

import pytest

from app.core.engine.arp_monitor import ArpMonitor


@pytest.mark.asyncio
async def test_arp_monitor_lifecycle():
    monitor = ArpMonitor()
    assert not monitor._is_running

    await monitor.start_monitoring()
    assert monitor._is_running

    # Idempotency
    await monitor.start_monitoring()
    assert monitor._is_running

    await monitor.stop_monitoring()
    assert not monitor._is_running


def test_arp_monitor_spoof_detection():
    monitor = ArpMonitor()
    ip = "192.168.1.10"
    mac_real = "AA:AA:AA:AA:AA:AA"
    mac_fake = "BB:BB:BB:BB:BB:BB"

    # First sighting - assume legit
    is_spoof = monitor.detect_spoof(ip, mac_real)
    assert is_spoof is False
    assert monitor._known_mappings[ip] == mac_real

    # Same MAC - all good
    is_spoof = monitor.detect_spoof(ip, mac_real)
    assert is_spoof is False

    # Different MAC - SPOOF!
    is_spoof = monitor.detect_spoof(ip, mac_fake)
    assert is_spoof is True


@pytest.mark.asyncio
async def test_arp_monitor_dummy_loop():
    # Verify the dummy loop runs and can be cancelled
    monitor = ArpMonitor()
    monitor._is_running = True

    # We mock asyncio.sleep to avoid waiting
    # Important: asyncio.sleep is awaitable, so our mock must be awaitable too
    # or return a value that can be awaited if used in `await asyncio.sleep(...)`
    # context.
    # However, here we are patching `asyncio.sleep` which is a coroutine function.
    # The best way to mock an async function is using AsyncMock or setting side_effect
    # to an async def.

    async def async_sleep_mock(*args, **kwargs):
        return None

    with patch("asyncio.sleep", side_effect=async_sleep_mock):
        task = asyncio.create_task(monitor._dummy_monitor_loop())

        # Let it "run" for a moment (yield control to the loop)
        # We use real sleep(0) to yield control, but our patched sleep will return
        # instantly inside the task. We need to ensure we are NOT calling the mocked
        # sleep here if we want real yielding?
        # Actually, since we patched asyncio.sleep globally in this block,
        # 'await asyncio.sleep(0)' below will ALSO call the mock and return instantly,
        # which is fine for yielding control in test loop.

        await asyncio.sleep(0)

        # Stop it
        monitor._is_running = False
        await asyncio.sleep(0)

        # It should complete/exit
        task.cancel()  # Just in case
        try:
            await task
        except asyncio.CancelledError:
            pass
