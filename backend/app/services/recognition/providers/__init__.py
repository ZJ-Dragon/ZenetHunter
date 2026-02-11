"""External recognition providers for device identification."""

from app.services.recognition.providers.base import RecognitionProvider
from app.services.recognition.providers.fingerbank import FingerbankProvider
from app.services.recognition.providers.macvendors import MACVendorsProvider

__all__ = [
    "RecognitionProvider",
    "MACVendorsProvider",
    "FingerbankProvider",
]
