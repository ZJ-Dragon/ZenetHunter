"""External recognition providers for device identification."""

from app.services.recognition.providers.base import RecognitionProvider
from app.services.recognition.providers.macvendors import MACVendorsProvider
from app.services.recognition.providers.fingerbank import FingerbankProvider

__all__ = [
    "RecognitionProvider",
    "MACVendorsProvider",
    "FingerbankProvider",
]
