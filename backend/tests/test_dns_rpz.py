import pytest

from app.core.engine.dns_rpz import DummyDnsRpzEngine


@pytest.mark.asyncio
async def test_dummy_dns_rpz():
    engine = DummyDnsRpzEngine()

    # Test adding zone
    res = await engine.add_zone("test_zone")
    assert res is True

    # Test adding rule
    res = await engine.add_rule("bad.com", "NXDOMAIN")
    assert res is True

    # Test removing rule
    res = await engine.remove_rule("bad.com")
    assert res is True
