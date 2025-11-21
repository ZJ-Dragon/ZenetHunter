import pytest
from unittest.mock import patch, MagicMock
from app.core.engine.factory import get_attack_engine
from app.core.engine.defense_factory import get_defense_engine
from app.core.engine.linux_defense import LinuxDefenseEngine
from app.core.engine.dummy_defense import DummyDefenseEngine
from app.models.defender import DefenseType


@pytest.mark.asyncio
async def test_defense_factory_root():
    with patch("os.geteuid", return_value=0):
        engine = get_defense_engine()
        assert isinstance(engine, LinuxDefenseEngine)


@pytest.mark.asyncio
async def test_defense_factory_non_root():
    with patch("os.geteuid", return_value=1000):
        engine = get_defense_engine()
        assert isinstance(engine, DummyDefenseEngine)


@pytest.mark.asyncio
async def test_linux_defense_synproxy():
    engine = LinuxDefenseEngine()
    # Mock the internal _run_cmd to avoid actual system calls
    engine._run_cmd = MagicMock(return_value=(0, "ok", ""))
    
    # Test Enable
    # We need to await the async method
    from asyncio import Future
    f = Future()
    f.set_result((0, "ok", ""))
    engine._run_cmd = MagicMock(return_value=f)
    
    await engine.enable_global_protection(DefenseType.SYN_PROXY)
    
    # Verify iptables calls were made
    # We expect 3 calls for enable
    assert engine._run_cmd.call_count == 3
    call_args = engine._run_cmd.call_args_list
    assert "iptables" in call_args[0][0][0]
    assert "SYNPROXY" in call_args[1][0][0]


@pytest.mark.asyncio
async def test_dummy_defense():
    engine = DummyDefenseEngine()
    await engine.enable_global_protection(DefenseType.SYN_PROXY)
    # Should just log, no error
    assert True

