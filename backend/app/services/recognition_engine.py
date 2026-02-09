"""Device recognition engine for multi-signal device identification."""

import json
import logging
import re
from pathlib import Path
from typing import Any

from app.services.device_model_lookup import get_device_model_lookup
from app.services.fingerprint_normalizer import FingerprintNormalizer
from app.services.keyword_extractor import KeywordExtractor, apply_confidence_delta
logger = logging.getLogger(__name__)


class RecognitionEngine:
    """Engine for identifying devices using multiple signals."""

    def __init__(self):
        self.normalizer = FingerprintNormalizer()
        self.model_lookup = get_device_model_lookup()
        self.local_rules: dict[str, dict[str, Any]] = {}
        self.keyword_extractor = KeywordExtractor()
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
                            f"Loaded recognition rule: "
                            f"{rule_data.get('fingerprint_key')}"
                        )
            except Exception as e:
                logger.error(f"Failed to load recognition rule {json_file}: {e}")

        logger.info(f"Loaded {len(self.local_rules)} local recognition rules")

    async def recognize_device(
        self, mac: str, fingerprint: dict[str, Any], existing_vendor: str | None = None
    ) -> dict[str, Any]:
        """
        Recognize device using multiple signals.

        Priority (local-only):
        1. Active probe evidence (HTTP, Telnet, SSH, SSDP - direct device responses)
        2. OUI-based vendor/model (local lookup, if MAC is non-random)
        3. DHCP fingerprint matching (local rules)
        4. Additional signals (mDNS/SSDP/UA/JA3)

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

        # Step 2: Active probe evidence (HTTP, Telnet, SSH, etc.)
        # These are direct responses from devices, high confidence
        active_probe_vendor = None
        active_probe_model = None
        active_probe_confidence = 0

        # Extract from HTTP responses
        http_title = fingerprint.get("http_title", "")
        http_server = fingerprint.get("http_server", "")
        http_meta_model = fingerprint.get("http_meta_model")
        http_meta_device = fingerprint.get("http_meta_device")
        http_meta_product = fingerprint.get("http_meta_product")

        # Extract from Telnet/SSH banners
        telnet_banner = fingerprint.get("telnet_banner", "")
        ssh_banner = fingerprint.get("ssh_banner", "")
        ssh_vendor = fingerprint.get("ssh_vendor")

        # Extract from SSDP (already implemented, but check here too)
        ssdp_manufacturer = fingerprint.get("ssdp_manufacturer")
        ssdp_model = fingerprint.get("ssdp_model")
        ssdp_model_name = fingerprint.get("ssdp_model_name")

        # Try to extract vendor/model from active probe data
        if ssdp_manufacturer or ssdp_model or ssdp_model_name:
            active_probe_vendor = ssdp_manufacturer
            active_probe_model = ssdp_model_name or ssdp_model
            active_probe_confidence = 85  # High confidence for SSDP
            evidence["sources"].append("active_probe_ssdp")
            evidence["matched_fields"].append("ssdp_device_description")
            evidence["weights"]["active_probe"] = 0.85
            logger.debug(
                f"SSDP device info for {mac}: "
                f"{active_probe_vendor}/{active_probe_model}"
            )

        # Extract from HTTP title/meta tags
        if http_title or http_meta_model or http_meta_device:
            # Try to parse device info from HTTP response
            if http_meta_model:
                active_probe_model = http_meta_model
                active_probe_confidence = max(active_probe_confidence, 75)
            if http_meta_device:
                active_probe_vendor = http_meta_device
                active_probe_confidence = max(active_probe_confidence, 75)
            if http_title and not active_probe_model:
                # Try to extract model from title (heuristic)
                # Example: "Router Admin - TP-Link TL-WR940N"
                title_lower = http_title.lower()
                if "tp-link" in title_lower or "tplink" in title_lower:
                    active_probe_vendor = "TP-Link"
                    # Try to extract model number
                    model_match = re.search(r"([A-Z]{2,3}-?[A-Z0-9-]+)", http_title)
                    if model_match:
                        active_probe_model = model_match.group(1)
                elif "netgear" in title_lower:
                    active_probe_vendor = "Netgear"
                elif "d-link" in title_lower or "dlink" in title_lower:
                    active_probe_vendor = "D-Link"
                elif "asus" in title_lower:
                    active_probe_vendor = "ASUS"
                elif "xiaomi" in title_lower or "mi" in title_lower:
                    active_probe_vendor = "Xiaomi"
                elif "huawei" in title_lower:
                    active_probe_vendor = "Huawei"

            if active_probe_vendor or active_probe_model:
                evidence["sources"].append("active_probe_http")
                evidence["matched_fields"].append("http_response")
                evidence["weights"]["active_probe"] = 0.75
                logger.debug(
                    f"HTTP device info for {mac}: "
                    f"{active_probe_vendor}/{active_probe_model}"
                )

        # Extract from Telnet/SSH banners
        if telnet_banner or ssh_banner:
            banner_text = (telnet_banner or ssh_banner).lower()
            # Common device identifiers in banners
            if "cisco" in banner_text:
                active_probe_vendor = "Cisco"
                active_probe_confidence = max(active_probe_confidence, 80)
            elif "huawei" in banner_text:
                active_probe_vendor = "Huawei"
                active_probe_confidence = max(active_probe_confidence, 80)
            elif "tp-link" in banner_text or "tplink" in banner_text:
                active_probe_vendor = "TP-Link"
                active_probe_confidence = max(active_probe_confidence, 80)

            if ssh_vendor:
                active_probe_vendor = ssh_vendor
                active_probe_confidence = max(active_probe_confidence, 80)

            if active_probe_vendor:
                evidence["sources"].append("active_probe_banner")
                evidence["matched_fields"].append("telnet_ssh_banner")
                evidence["weights"]["active_probe"] = 0.8
                logger.debug(
                    f"Banner device info for {mac}: vendor={active_probe_vendor}"
                )

        # Step 3: DHCP fingerprint matching (local rules)
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

        # Step 3: Combine results with weighted confidence (local only)
        final_vendor = vendor_guess or dhcp_vendor
        final_model = model_guess or dhcp_model

        # Calculate combined confidence (weighted average)
        confidences = []
        if active_probe_confidence > 0:
            confidences.append(("active_probe", active_probe_confidence, 0.85))
        if oui_confidence > 0:
            confidences.append(("oui", oui_confidence, 0.8))
        if dhcp_confidence > 0:
            confidences.append(("dhcp", dhcp_confidence, 0.7))

        if confidences:
            # Weighted average
            total_weight = sum(w for _, _, w in confidences)
            weighted_sum = sum(c * w for _, c, w in confidences)
            final_confidence = min(100, int(weighted_sum / total_weight))
        else:
            final_confidence = 0

        # Step 6: Keyword dictionary influence
        keyword_tokens = self.keyword_extractor.extract(fingerprint)
        keyword_hits = self.keyword_extractor.match_rules(keyword_tokens, fingerprint)
        evidence["keyword_hits"] = keyword_hits
        final_name: str | None = None
        if keyword_hits:
            evidence["sources"].append("dictionary")
            evidence["matched_fields"].append("keyword_dictionary")
            final_confidence, delta_total = apply_confidence_delta(
                final_confidence, keyword_hits
            )
            evidence.setdefault("confidence_breakdown", {})
            evidence["confidence_breakdown"]["dictionary_delta"] = delta_total
            merged_infer: dict[str, str] = {}
            for hit in sorted(
                keyword_hits,
                key=lambda h: (-int(h.get("priority", 0)), h.get("rule_id", "")),
            ):
                infer = hit.get("infer") or {}
                for key in ("vendor", "product", "category", "os", "name"):
                    if key not in merged_infer and infer.get(key):
                        merged_infer[key] = infer[key]
            if merged_infer:
                evidence["dictionary_infer"] = merged_infer
            top_hit = sorted(
                keyword_hits,
                key=lambda h: (-int(h.get("priority", 0)), h.get("rule_id", "")),
            )[0]
            infer = top_hit.get("infer", {}) or {}
            if not final_vendor and infer.get("vendor"):
                final_vendor = infer.get("vendor")
            if not final_model and infer.get("product"):
                final_model = infer.get("product")
            if infer.get("name"):
                final_name = infer.get("name")

        # Add evidence summary
        evidence["confidence_breakdown"] = {
            "active_probe": active_probe_confidence,
            "oui": oui_confidence,
            "dhcp": dhcp_confidence,
            "combined": final_confidence,
            **evidence.get("confidence_breakdown", {}),
        }

        result = {
            "best_guess_vendor": final_vendor,
            "best_guess_model": final_model,
            "best_guess_name": final_name,
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
