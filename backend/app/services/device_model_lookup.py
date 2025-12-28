"""Device model lookup service based on MAC address and vendor information."""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DeviceModelLookup:
    """
    Service to lookup device models from MAC addresses.
    Uses vendor-specific lookup tables stored in JSON files.
    """

    def __init__(self):
        """Initialize the lookup service and load vendor databases."""
        self.vendor_db: dict[str, dict] = {}
        self._load_vendor_databases()

    def _load_vendor_databases(self):
        """Load all vendor lookup tables from JSON files."""
        # Get the path to the vendors directory
        # This file is in backend/app/services/, so we need to go up one level
        current_dir = Path(__file__).parent
        vendors_dir = current_dir.parent / "data" / "vendors"

        if not vendors_dir.exists():
            logger.warning(f"Vendors directory not found: {vendors_dir}")
            return

        # Load all JSON files in the vendors directory
        for json_file in vendors_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    vendor_data = json.load(f)
                    vendor_name = vendor_data.get("vendor", "").lower()
                    if vendor_name:
                        self.vendor_db[vendor_name] = vendor_data
                        logger.debug(
                            f"Loaded vendor database: {vendor_name} "
                            f"({len(vendor_data.get('models', {}))} MAC prefixes)"
                        )
            except Exception as e:
                logger.error(f"Failed to load vendor database {json_file}: {e}")

        logger.info(f"Loaded {len(self.vendor_db)} vendor databases")

    def _extract_oui(self, mac: str) -> str:
        """
        Extract OUI (first 3 octets) from MAC address.
        
        Args:
            mac: MAC address in format XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
            
        Returns:
            OUI in format XX:XX:XX (uppercase)
        """
        # Normalize MAC address
        mac_normalized = mac.upper().replace("-", ":")
        # Extract first 3 octets (OUI)
        parts = mac_normalized.split(":")
        if len(parts) >= 3:
            return ":".join(parts[:3])
        return ""

    def lookup_model(self, mac: str, vendor: Optional[str] = None) -> Optional[str]:
        """
        Lookup device model from MAC address.
        
        Args:
            mac: MAC address of the device
            vendor: Optional vendor name (if known, speeds up lookup)
            
        Returns:
            Device model name if found, None otherwise
        """
        if not mac:
            return None

        oui = self._extract_oui(mac)
        if not oui:
            return None

        # If vendor is provided, try that vendor's database first
        if vendor:
            vendor_lower = vendor.lower()
            if vendor_lower in self.vendor_db:
                models = self.vendor_db[vendor_lower].get("models", {})
                if oui in models:
                    model_list = models[oui]
                    # Return the first model in the list (most common)
                    if model_list and len(model_list) > 0:
                        return model_list[0]
                    return None

        # Otherwise, search all vendor databases
        for vendor_name, vendor_data in self.vendor_db.items():
            models = vendor_data.get("models", {})
            if oui in models:
                model_list = models[oui]
                if model_list and len(model_list) > 0:
                    # Return the first model in the list
                    return model_list[0]

        return None

    def lookup_vendor_and_model(self, mac: str) -> tuple[Optional[str], Optional[str]]:
        """
        Lookup both vendor and model from MAC address.
        
        Args:
            mac: MAC address of the device
            
        Returns:
            Tuple of (vendor, model) if found, (None, None) otherwise
        """
        if not mac:
            return None, None

        oui = self._extract_oui(mac)
        if not oui:
            return None, None

        # Search all vendor databases
        for vendor_name, vendor_data in self.vendor_db.items():
            models = vendor_data.get("models", {})
            if oui in models:
                model_list = models[oui]
                vendor = vendor_data.get("vendor", vendor_name.title())
                model = model_list[0] if model_list and len(model_list) > 0 else None
                return vendor, model

        return None, None


# Global singleton instance
_lookup_instance: Optional[DeviceModelLookup] = None


def get_device_model_lookup() -> DeviceModelLookup:
    """Get the global DeviceModelLookup instance."""
    global _lookup_instance
    if _lookup_instance is None:
        _lookup_instance = DeviceModelLookup()
    return _lookup_instance
