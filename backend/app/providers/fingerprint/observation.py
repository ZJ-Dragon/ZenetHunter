"""Fingerprint extraction from normalized probe observations."""

from __future__ import annotations

from app.domain.interfaces.providers import (
    DiscoveredDevice,
    FingerprintExtractor,
    ProbeObservation,
)
from app.services.fingerprint_normalizer import get_fingerprint_normalizer


class ObservationFingerprintExtractor(FingerprintExtractor):
    """Merge probe observations into a normalized fingerprint payload."""

    name = "observation-fingerprint-extractor"

    def __init__(self):
        self.normalizer = get_fingerprint_normalizer()

    def extract(
        self,
        device: DiscoveredDevice,
        observations: list[ProbeObservation],
    ) -> dict[str, object]:
        fingerprint: dict[str, object] = {}
        hostname = device.metadata.get("hostname")
        if hostname:
            fingerprint["dhcp_opt12_hostname"] = hostname

        for observation in observations:
            fingerprint.update(observation.raw_fields)

        normalized = self.normalizer.normalize_fingerprint(fingerprint)
        normalized["ip"] = device.ip
        normalized["mac"] = device.mac
        return normalized


_extractor_instance: ObservationFingerprintExtractor | None = None


def get_observation_fingerprint_extractor() -> ObservationFingerprintExtractor:
    """Return the singleton observation fingerprint extractor."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = ObservationFingerprintExtractor()
    return _extractor_instance
