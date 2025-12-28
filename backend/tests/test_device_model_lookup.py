"""Tests for device model lookup service."""

import pytest
from unittest.mock import patch, mock_open

from app.services.device_model_lookup import DeviceModelLookup


def test_extract_oui():
    """Test OUI extraction from MAC address."""
    lookup = DeviceModelLookup()
    
    # Test with colon separator
    assert lookup._extract_oui("AA:BB:CC:DD:EE:FF") == "AA:BB:CC"
    assert lookup._extract_oui("00:11:22:33:44:55") == "00:11:22"
    
    # Test with hyphen separator
    assert lookup._extract_oui("AA-BB-CC-DD-EE-FF") == "AA:BB:CC"
    
    # Test case insensitivity
    assert lookup._extract_oui("aa:bb:cc:dd:ee:ff") == "AA:BB:CC"
    
    # Test invalid MAC
    assert lookup._extract_oui("invalid") == ""


def test_lookup_model_no_vendor():
    """Test model lookup without vendor info."""
    lookup = DeviceModelLookup()
    
    # Test with empty vendor database (no models loaded)
    result = lookup.lookup_model("00:11:22:33:44:55")
    # Should return None if no vendor DB is loaded or OUI not found
    assert result is None or isinstance(result, str)


def test_lookup_model_with_vendor():
    """Test model lookup with vendor info."""
    lookup = DeviceModelLookup()
    
    # Mock vendor database
    lookup.vendor_db = {
        "testvendor": {
            "vendor": "TestVendor",
            "models": {
                "AA:BB:CC": ["Model1", "Model2"]
            }
        }
    }
    
    # Test lookup with matching vendor and OUI
    result = lookup.lookup_model("AA:BB:CC:DD:EE:FF", vendor="TestVendor")
    assert result == "Model1"
    
    # Test lookup with non-matching vendor
    result = lookup.lookup_model("AA:BB:CC:DD:EE:FF", vendor="OtherVendor")
    assert result == "Model1"  # Should still find it by searching all vendors


def test_lookup_vendor_and_model():
    """Test vendor and model lookup."""
    lookup = DeviceModelLookup()
    
    # Mock vendor database
    lookup.vendor_db = {
        "testvendor": {
            "vendor": "TestVendor",
            "models": {
                "AA:BB:CC": ["Model1", "Model2"]
            }
        }
    }
    
    vendor, model = lookup.lookup_vendor_and_model("AA:BB:CC:DD:EE:FF")
    assert vendor == "TestVendor"
    assert model == "Model1"
    
    # Test with non-existent MAC
    vendor, model = lookup.lookup_vendor_and_model("FF:FF:FF:FF:FF:FF")
    assert vendor is None
    assert model is None


def test_lookup_model_empty_mac():
    """Test lookup with empty MAC address."""
    lookup = DeviceModelLookup()
    
    assert lookup.lookup_model("") is None
    assert lookup.lookup_model(None) is None


def test_get_device_model_lookup_singleton():
    """Test that get_device_model_lookup returns singleton."""
    from app.services.device_model_lookup import get_device_model_lookup
    
    instance1 = get_device_model_lookup()
    instance2 = get_device_model_lookup()
    
    assert instance1 is instance2
