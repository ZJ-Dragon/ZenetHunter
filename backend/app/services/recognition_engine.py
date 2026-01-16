"""Device recognition engine for multi-signal device identification."""

import json
import logging
from pathlib import Path
from typing import Any

from app.services.device_model_lookup import get_device_model_lookup
from app.services.fingerprint_normalizer import FingerprintNormalizer

logger = logging.getLogger(__name__)


class RecognitionEngine:
    """Engine for identifying devices using multiple signals."""

    def __init__(self):
        self.normalizer = FingerprintNormalizer()
        self.model_lookup = get_device_model_lookup()
        self.local_rules: dict[str, dict[str, Any]] = {}
        self._load_local_rules()

    def _load_local_rules(self) -> None:
        """Load local recognition rules from JSON files."""
        # Get path to recognition rules directory
        current_dir = Path(__file__).parent
        rules_dir = current_dir.parent / "data" / "recognition_rules"

        if not rules_dir.exists():
            logger.info(f"Recognition rules directory not found: {rules_dir}")
            return

        # Load all JSON rule files
        for json_file in rules_dir.glob("*.json"):
            try:
                with open(json_file, encoding="utf-8") as f:
                    rule_data = json.load(f)
                    # Use fingerprint key as rule key
                    if "fingerprint_key" in rule_data:
                        self.local_rules[rule_data["fingerprint_key"]] = rule_data
                        logger.debug(
                            f"Loaded recognition rule: {rule_data.get('fingerprint_key')}"
                        )
            except Exception as e:
                logger.error(f"Failed to load recognition rule {json_file}: {e}")

        logger.info(f"Loaded {len(self.local_rules)} local recognition rules")

    def recognize_device(
        self, mac: str, fingerprint: dict[str, Any], existing_vendor: str | None = None
    ) -> dict[str, Any]:
        """
        Recognize device using multiple signals.

        Priority:
        1. OUI-based vendor/model (if MAC is non-random)
        2. DHCP fingerprint matching (local rules)
        3. Optional: Fingerbank query (if enabled)
        4. Optional: Additional signals (mDNS/SSDP/UA/JA3)

        Args:
            mac: Device MAC address
            fingerprint: Dictionary with fingerprint signals
            existing_vendor: Existing vendor from OUI lookup (if available)

        Returns:
            Dictionary with:
                - best_guess_vendor: Vendor name or None
                - best_guess_model: Model name or None
                - confidence: 0-100 confidence score
                - evidence: JSON dict with matched fields and sources
        """
        evidence: dict[str, Any] = {
            "sources": [],
            "matched_fields": [],
            "weights": {},
        }

        # Step 1: OUI-based recognition (highest priority if MAC is non-random)
        vendor_guess = existing_vendor
        model_guess = None
        oui_confidence = 0

        if mac and not self._is_random_mac(mac):
            vendor, model = self.model_lookup.lookup_vendor_and_model(mac)
            if vendor:
                vendor_guess = vendor
                model_guess = model
                oui_confidence = 80  # High confidence for OUI match
                evidence["sources"].append("oui")
                evidence["matched_fields"].append("mac_oui")
                evidence["weights"]["oui"] = 0.8
                logger.debug(f"OUI match for {mac}: {vendor}/{model}")

        # Step 2: DHCP fingerprint matching (local rules)
        fingerprint_key = self.normalizer.compute_fingerprint_key(fingerprint)
        dhcp_confidence = 0
        dhcp_vendor = None
        dhcp_model = None

        if fingerprint_key and fingerprint_key != "empty":
            matched_rule = self.local_rules.get(fingerprint_key)
            if matched_rule:
                dhcp_vendor = matched_rule.get("vendor")
                dhcp_model = matched_rule.get("model")
                dhcp_confidence = matched_rule.get("confidence", 70)
                evidence["sources"].append("local_dhcp")
                evidence["matched_fields"].extend(
                    [
                        f
                        for f in [
                            "dhcp_opt55_prl",
                            "dhcp_opt60_vci",
                            "dhcp_opt12_hostname",
                        ]
                        if fingerprint.get(f)
                    ]
                )
                evidence["weights"]["dhcp"] = 0.7
                logger.debug(
                    f"DHCP fingerprint match for {mac}: "
                    f"{dhcp_vendor}/{dhcp_model} (confidence: {dhcp_confidence})"
                )

        # Step 3: Combine results with weighted confidence
        final_vendor = vendor_guess or dhcp_vendor
        final_model = model_guess or dhcp_model

        # Calculate combined confidence
        if oui_confidence > 0 and dhcp_confidence > 0:
            # Both signals agree - boost confidence
            if vendor_guess == dhcp_vendor:
                final_confidence = min(
                    100, int((oui_confidence + dhcp_confidence) * 0.6)
                )
            else:
                # Signals disagree - use higher confidence but reduce
                final_confidence = max(oui_confidence, dhcp_confidence) - 20
        elif oui_confidence > 0:
            final_confidence = oui_confidence
        elif dhcp_confidence > 0:
            final_confidence = dhcp_confidence
        else:
            final_confidence = 0

        # Add evidence summary
        evidence["confidence_breakdown"] = {
            "oui": oui_confidence,
            "dhcp": dhcp_confidence,
            "combined": final_confidence,
        }

        result = {
            "best_guess_vendor": final_vendor,
            "best_guess_model": final_model,
            "confidence": final_confidence,
            "evidence": evidence,
        }

        logger.info(
            f"Recognition result for {mac}: "
            f"{final_vendor}/{final_model} (confidence: {final_confidence}%)"
        )

        return result

    def _is_random_mac(self, mac: str) -> bool:
        """
        Check if MAC address is likely randomized (privacy MAC).

        Randomized MACs typically have the locally administered bit set
        (second hex digit is 2, 6, A, or E).

        Args:
            mac: MAC address string

        Returns:
            True if MAC appears to be randomized
        """
        if not mac or len(mac) < 2:
            return False

        # Normalize MAC (remove separators, uppercase)
        mac_clean = mac.replace(":", "").replace("-", "").upper()
        if len(mac_clean) < 2:
            return False

        # Check second hex digit (locally administered bit)
        second_char = mac_clean[1]
        return second_char in ("2", "6", "A", "E")


# Global singleton instance
_engine_instance: RecognitionEngine | None = None


def get_recognition_engine() -> RecognitionEngine:
    """Get the global RecognitionEngine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RecognitionEngine()
    return _engine_instance
