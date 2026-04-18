"""Fingerprint extractor providers."""

from app.providers.fingerprint.observation import (
    ObservationFingerprintExtractor,
    get_observation_fingerprint_extractor,
)

__all__ = [
    "ObservationFingerprintExtractor",
    "get_observation_fingerprint_extractor",
]
