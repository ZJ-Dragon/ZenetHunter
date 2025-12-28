from unittest.mock import MagicMock, patch

import pytest

from app.core.engine.defense_factory import get_defense_engine
from app.core.engine.dummy_defense import DummyDefenseEngine
from app.core.engine.linux_defense import LinuxDefenseEngine
from app.core.platform.detect import Platform, PlatformFeatures
from app.models.defender import DefenseType


@pytest.mark.asyncio
async def test_defense_factory_root():

    # Create a mock PlatformFeatures with root=True and Linux platform
    mock_features = MagicMock(spec=PlatformFeatures)
    mock_features.is_root = True
    mock_features.platform = Platform.LINUX
    mock_features.has_pfctl = False
    mock_features.has_netsh = False

    with patch(
        "app.core.engine.defense_factory.get_platform_features",
        return_value=mock_features,
    ):
        # Also need to mock is_linux() to return True
        with patch("app.core.engine.defense_factory.is_linux", return_value=True):
            engine = get_defense_engine()
            assert isinstance(
                engine, LinuxDefenseEngine
            ), f"Expected LinuxDefenseEngine, got {type(engine).__name__}"


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
async def test_linux_defense_udp_limit():
    engine = LinuxDefenseEngine()

    from asyncio import Future

    f = Future()
    f.set_result((0, "ok", ""))
    engine._run_cmd = MagicMock(return_value=f)

    await engine.enable_global_protection(DefenseType.UDP_RATE_LIMIT)

    # Verify tc calls
    # Expecting 6 commands (clean, root, classes, filter)
    assert engine._run_cmd.call_count == 6
    call_args = engine._run_cmd.call_args_list

    # Check critical commands
    assert "tc" in call_args[1][0][0]
    assert "htb" in call_args[1][0][0]
    # Check UDP filter
    filter_cmd = call_args[5][0][0]
    assert "protocol" in filter_cmd
    assert "17" in filter_cmd  # UDP proto


@pytest.mark.asyncio
async def test_dummy_defense():
    engine = DummyDefenseEngine()
    await engine.enable_global_protection(DefenseType.SYN_PROXY)
    await engine.enable_global_protection(DefenseType.UDP_RATE_LIMIT)
    # Should just log, no error
    assert True
