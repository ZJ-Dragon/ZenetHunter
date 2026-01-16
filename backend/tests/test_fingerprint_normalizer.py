"""Tests for fingerprint normalizer."""

from app.services.fingerprint_normalizer import FingerprintNormalizer


def test_normalize_hostname():
    """Test hostname normalization."""
    assert FingerprintNormalizer.normalize_hostname("MyDevice") == "mydevice"
    assert (
        FingerprintNormalizer.normalize_hostname("  MyDevice.local.  ")
        == "mydevice.local"
    )
    assert FingerprintNormalizer.normalize_hostname(None) is None
    assert FingerprintNormalizer.normalize_hostname("") is None


def test_normalize_opt55_prl():
    """Test Option 55 PRL normalization."""
    # Comma-separated string
    assert FingerprintNormalizer.normalize_opt55_prl("1,3,6,15") == "1,3,6,15"
    assert FingerprintNormalizer.normalize_opt55_prl("15,3,1,6") == "1,3,6,15"  # Sorted
    # List of integers
    assert FingerprintNormalizer.normalize_opt55_prl([1, 3, 6, 15]) == "1,3,6,15"
    assert (
        FingerprintNormalizer.normalize_opt55_prl([15, 3, 1, 6]) == "1,3,6,15"
    )  # Sorted
    # Edge cases
    assert FingerprintNormalizer.normalize_opt55_prl(None) is None
    assert FingerprintNormalizer.normalize_opt55_prl("") is None
    assert FingerprintNormalizer.normalize_opt55_prl([]) is None


def test_normalize_opt60_vci():
    """Test Option 60 VCI normalization."""
    assert (
        FingerprintNormalizer.normalize_opt60_vci("Cisco:Codec:1.0")
        == "Cisco:Codec:1.0"
    )
    assert (
        FingerprintNormalizer.normalize_opt60_vci("  Cisco:Codec:1.0  ")
        == "Cisco:Codec:1.0"
    )
    assert FingerprintNormalizer.normalize_opt60_vci(None) is None
    assert FingerprintNormalizer.normalize_opt60_vci("") is None


def test_normalize_user_agent():
    """Test User-Agent normalization."""
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    assert FingerprintNormalizer.normalize_user_agent(ua) == ua
    assert FingerprintNormalizer.normalize_user_agent(f"  {ua}  ") == ua
    assert FingerprintNormalizer.normalize_user_agent(None) is None


def test_normalize_ja3():
    """Test JA3 normalization."""
    ja3_hash = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"
    normalized = FingerprintNormalizer.normalize_ja3(ja3_hash)
    assert normalized == ja3_hash.lower()
    # MD5 hash format (32 hex chars)
    md5_hash = "ABCD1234EF567890ABCD1234EF567890"
    assert FingerprintNormalizer.normalize_ja3(md5_hash) == md5_hash.lower()
    assert FingerprintNormalizer.normalize_ja3(None) is None


def test_normalize_fingerprint():
    """Test full fingerprint normalization."""
    fingerprint = {
        "dhcp_opt12_hostname": "  MyDevice.local.  ",
        "dhcp_opt55_prl": "15,3,1,6",
        "dhcp_opt60_vci": "  Cisco:Codec:1.0  ",
        "user_agent": "  Mozilla/5.0  ",
        "ja3": "ABCD1234",
        "mdns_services": ["_http._tcp", "_ssh._tcp"],
    }

    normalized = FingerprintNormalizer.normalize_fingerprint(fingerprint)

    assert normalized["dhcp_opt12_hostname"] == "mydevice.local"
    assert normalized["dhcp_opt55_prl"] == "1,3,6,15"
    assert normalized["dhcp_opt60_vci"] == "Cisco:Codec:1.0"
    assert normalized["user_agent"] == "Mozilla/5.0"
    assert normalized["ja3"] == "abcd1234"
    assert normalized["mdns_services"] == ["_http._tcp", "_ssh._tcp"]


def test_compute_fingerprint_key():
    """Test fingerprint key computation."""
    fingerprint = {
        "dhcp_opt55_prl": "1,3,6,15",
        "dhcp_opt60_vci": "Cisco:Codec:1.0",
        "dhcp_opt12_hostname": "mydevice",
        "ja3": "abcd1234",
    }

    key = FingerprintNormalizer.compute_fingerprint_key(fingerprint)

    # Key should contain all signals, sorted
    assert "prl:1,3,6,15" in key
    assert "vci:Cisco:Codec:1.0" in key
    assert "host:mydevice" in key
    assert "ja3:abcd1234" in key

    # Empty fingerprint
    empty_key = FingerprintNormalizer.compute_fingerprint_key({})
    assert empty_key == "empty"
