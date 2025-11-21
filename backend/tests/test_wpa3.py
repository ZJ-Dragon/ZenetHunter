import pytest
from app.core.engine.dummy_ap import DummyAccessPointManager
from app.models.wpa3 import EapMethod, RadiusConfig, VlanPolicy, Wpa3Config, WpaMode

@pytest.mark.asyncio
async def test_dummy_ap_manager():
    manager = DummyAccessPointManager()
    
    # Test capabilities
    assert await manager.check_capabilities() is True
    
    # Test WPA3 configuration
    config = Wpa3Config(
        mode=WpaMode.WPA3_ENTERPRISE,
        ssid="ZenetHunter-Secure",
        radius=RadiusConfig(
            server_ip="192.168.1.10",
            port=1812,
            secret="test-secret"
        ),
        eap_method=EapMethod.PEAP,
        default_vlan=VlanPolicy(vlan_id=100, name="Authenticated Users")
    )
    
    result = await manager.configure_wpa3(config)
    assert result is True
    
    # Test VLAN assignment
    result = await manager.assign_vlan("AA:BB:CC:DD:EE:FF", 100)
    assert result is True
    
    # Test VLAN removal
    result = await manager.remove_vlan_assignment("AA:BB:CC:DD:EE:FF")
    assert result is True

