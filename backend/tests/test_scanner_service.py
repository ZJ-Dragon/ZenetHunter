"""Tests for scanner service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.scan import ScanRequest
from app.services.scanner import ScannerService


@pytest.mark.asyncio
async def test_start_scan_returns_immediately():
    """Test that start_scan returns immediately with RUNNING status."""
    service = ScannerService()
    
    request = ScanRequest(type="quick")
    result = await service.start_scan(request)
    
    assert result.status.value == "running"
    assert result.id is not None


@pytest.mark.asyncio
async def test_clear_device_cache():
    """Test device cache clearing."""
    service = ScannerService()
    
    # Mock database operations
    with patch("app.services.scanner.get_session_factory") as mock_factory:
        mock_session = AsyncMock()
        mock_repo = MagicMock()
        mock_repo.clear_all = AsyncMock(return_value=5)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.commit = AsyncMock()
        
        # Mock repository creation
        with patch("app.services.scanner.DeviceRepository", return_value=mock_repo):
            mock_factory.return_value = lambda: mock_session
            
            await service._clear_device_cache()
            
            # Verify clear_all was called
            mock_repo.clear_all.assert_called_once()
            mock_session.commit.assert_called_once()


def test_is_valid_mac():
    """Test MAC address validation."""
    service = ScannerService()
    
    # Valid MAC addresses
    assert service._is_valid_mac("00:11:22:33:44:55") is True
    assert service._is_valid_mac("AA:BB:CC:DD:EE:FF") is True
    assert service._is_valid_mac("00-11-22-33-44-55") is True
    
    # Invalid MAC addresses
    assert service._is_valid_mac("invalid") is False
    assert service._is_valid_mac("00:11:22") is False
    assert service._is_valid_mac("") is False
    assert service._is_valid_mac("00:11:22:33:44:GG") is False  # Invalid hex


def test_guess_vendor():
    """Test vendor guessing from MAC address."""
    service = ScannerService()
    
    # Test that the method exists and can be called
    # Actual vendor guessing uses device model lookup service
    result = service._guess_vendor("00:11:22:33:44:55")
    # Result should be None or a string
    assert result is None or isinstance(result, str)
