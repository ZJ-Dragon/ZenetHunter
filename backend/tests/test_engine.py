from unittest.mock import patch

import pytest

from app.core.engine.dummy import DummyAttackEngine
from app.core.engine.factory import get_attack_engine
from app.core.engine.scapy import ScapyAttackEngine
from app.models.attack import AttackType


def test_dummy_engine_permissions():
    engine = DummyAttackEngine()
    assert engine.check_permissions() is True


@pytest.mark.asyncio
async def test_dummy_engine_start_stop():
    engine = DummyAttackEngine()
    # Should just log and return, no errors
    await engine.start_attack("00:11:22:33:44:55", AttackType.KICK, 5)
    await engine.stop_attack("00:11:22:33:44:55")


def test_scapy_engine_permissions_root():
    with patch("os.geteuid", return_value=0):
        engine = ScapyAttackEngine()
        assert engine.check_permissions() is True


def test_scapy_engine_permissions_non_root():
    with patch("os.geteuid", return_value=1000):
        engine = ScapyAttackEngine()
        assert engine.check_permissions() is False


@pytest.mark.asyncio
async def test_scapy_engine_start_no_permissions():
    engine = ScapyAttackEngine()
    # Mock check_permissions to False
    with patch.object(engine, "check_permissions", return_value=False):
        with pytest.raises(PermissionError):
            await engine.start_attack("00:11:22:33:44:55", AttackType.KICK, 5)


def test_factory_fallback():
    # Mock Scapy engine permissions to False -> Should return Dummy
    with patch.object(ScapyAttackEngine, "check_permissions", return_value=False):
        engine = get_attack_engine()
        assert isinstance(engine, DummyAttackEngine)


def test_factory_scapy():
    # Mock Scapy engine permissions to True -> Should return Scapy
    with patch.object(ScapyAttackEngine, "check_permissions", return_value=True):
        engine = get_attack_engine()
        assert isinstance(engine, ScapyAttackEngine)
