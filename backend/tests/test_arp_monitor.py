import pytest
from unittest.mock import MagicMock, patch
from app.core.engine.arp_monitor import ArpMonitor
import asyncio

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
    with patch('asyncio.sleep', new_callable=MagicMock) as mock_sleep:
        mock_sleep.return_value = None # Immediate return
        
        task = asyncio.create_task(monitor._dummy_monitor_loop())
        
        # Let it "run" for a moment
        await asyncio.sleep(0)
        
        # Stop it
        monitor._is_running = False
        await asyncio.sleep(0)
        
        # It should complete/exit
        task.cancel() # Just in case
        try:
            await task
        except asyncio.CancelledError:
            pass
