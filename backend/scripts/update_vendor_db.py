#!/usr/bin/env python3
"""
Script to update MAC address vendor database from online sources.

This script fetches MAC address OUI (Organizationally Unique Identifier) 
to vendor mappings from IEEE OUI database and updates the vendor JSON files.
"""

import json
import logging
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, List
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# IEEE OUI database URL
IEEE_OUI_URL = "https://standards-oui.ieee.org/oui/oui.txt"

# Vendor directory
VENDOR_DIR = Path(__file__).parent.parent / "app" / "data" / "vendors"


def parse_oui_content(content: str) -> Dict[str, str]:
    """
    Parse OUI database content and extract OUI to vendor mappings.
    
    Args:
        content: Raw OUI database text content
        
    Returns:
        Dictionary mapping OUI (format: XX-XX-XX) to vendor name
    """
    oui_map = {}
    
    logger.info(f"Parsing OUI database content ({len(content)} bytes)")
    
    # Parse OUI database format
    # Format: XX-XX-XX   (hex)     Vendor Name
    pattern = re.compile(r'^([0-9A-F]{2})-([0-9A-F]{2})-([0-9A-F]{2})\s+\(hex\)\s+(.+)$', re.IGNORECASE)
    
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        match = pattern.match(line)
        if match:
            oui = f"{match.group(1)}-{match.group(2)}-{match.group(3)}".upper()
            vendor = match.group(4).strip()
            vendor = normalize_vendor_name(vendor)
            
            if vendor:
                oui_map[oui] = vendor
                
    logger.info(f"Parsed {len(oui_map)} OUI entries from database")
    return oui_map


def normalize_vendor_name(vendor: str) -> str:
    """Normalize vendor name for consistent matching."""
    # Remove common suffixes and normalize
    vendor = vendor.strip()
    vendor = re.sub(r'\s+Inc\.?$', '', vendor, flags=re.IGNORECASE)
    vendor = re.sub(r'\s+Corp\.?$', '', vendor, flags=re.IGNORECASE)
    vendor = re.sub(r'\s+Ltd\.?$', '', vendor, flags=re.IGNORECASE)
    vendor = re.sub(r'\s+LLC\.?$', '', vendor, flags=re.IGNORECASE)
    vendor = re.sub(r'\s+Co\.?$', '', vendor, flags=re.IGNORECASE)
    return vendor.strip()


def fetch_ieee_oui_database() -> Dict[str, str]:
    """
    Fetch OUI to vendor mapping from IEEE OUI database.
    
    Returns:
        Dictionary mapping OUI (format: XX-XX-XX) to vendor name
    """
    oui_map = {}
    
    try:
        logger.info(f"Fetching IEEE OUI database from {IEEE_OUI_URL}")
        # Use more realistic browser headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/plain,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        req = Request(IEEE_OUI_URL, headers=headers)
        
        import time
        time.sleep(1)  # Add a small delay to be more polite
        
        with urlopen(req, timeout=60) as response:
            # Handle gzip encoding if needed
            import gzip
            content_bytes = response.read()
            
            # Try to detect if content is gzipped
            try:
                content = gzip.decompress(content_bytes).decode('utf-8', errors='ignore')
            except (gzip.BadGzipFile, OSError):
                content = content_bytes.decode('utf-8', errors='ignore')
        
        # Parse the content
        oui_map = parse_oui_content(content)
        
    except HTTPError as e:
        if e.code == 418:
            logger.warning("Server returned 418 (likely anti-bot protection). Trying alternative method...")
            # Try using requests library if available, or suggest manual download
            try:
                import requests
                logger.info("Using requests library as fallback...")
                response = requests.get(IEEE_OUI_URL, headers=headers, timeout=60)
                response.raise_for_status()
                content = response.text
                oui_map = parse_oui_content(content)
                return oui_map
            except ImportError:
                logger.error("requests library not available. Please install it: pip install requests")
                logger.error("Alternatively, manually download the OUI database from:")
                logger.error("https://standards-oui.ieee.org/oui/oui.txt")
                logger.error("and save it as 'oui.txt' in the scripts directory, then run:")
                logger.error("python scripts/update_vendor_db.py --local oui.txt")
                return {}
            except Exception as e2:
                logger.error(f"Alternative method also failed: {e2}")
                return {}
        else:
            logger.error(f"Failed to fetch IEEE OUI database: HTTP {e.code} - {e.reason}")
            return {}
    except URLError as e:
        logger.error(f"Failed to fetch IEEE OUI database (network error): {e.reason}")
        return {}
    except Exception as e:
        logger.error(f"Error parsing IEEE OUI database: {e}", exc_info=True)
        return {}
    
    return oui_map


def group_ouis_by_vendor(oui_map: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Group OUI prefixes by vendor name.
    
    Args:
        oui_map: Dictionary mapping OUI to vendor name
        
    Returns:
        Dictionary mapping vendor name to list of OUI prefixes
    """
    vendor_ouis: Dict[str, List[str]] = {}
    
    for oui, vendor in oui_map.items():
        if vendor not in vendor_ouis:
            vendor_ouis[vendor] = []
        vendor_ouis[vendor].append(oui)
    
    return vendor_ouis


def update_vendor_file(vendor_name: str, oui_list: List[str], existing_file: Path = None):
    """
    Update or create a vendor JSON file with OUI mappings.
    
    Args:
        vendor_name: Name of the vendor
        oui_list: List of OUI prefixes (format: XX-XX-XX)
        existing_file: Optional path to existing vendor file
    """
    vendor_file = VENDOR_DIR / f"{vendor_name.lower().replace(' ', '_')}.json"
    
    # Load existing file if it exists
    existing_data = {}
    if existing_file and existing_file.exists():
        try:
            with open(existing_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load existing file {existing_file}: {e}")
    
    # Convert OUI format from XX-XX-XX to XX:XX:XX for JSON keys
    models = {}
    for oui in oui_list:
        oui_colon = oui.replace('-', ':')
        # Use generic device names based on vendor
        if vendor_name.lower() in ['apple', 'samsung', 'huawei', 'xiaomi', 'oppo', 'vivo', 'oneplus', 'lg', 'meizu', 'honor', 'redmi']:
            models[oui_colon] = [f"{vendor_name} Phone", f"{vendor_name} Tablet"]
        elif vendor_name.lower() in ['tplink', 'd-link', 'netgear', 'asus', 'cisco']:
            models[oui_colon] = [f"{vendor_name} Router", f"{vendor_name} Modem"]
        else:
            models[oui_colon] = [f"{vendor_name} Device"]
    
    # Merge with existing models if any
    if 'models' in existing_data:
        existing_data['models'].update(models)
    else:
        existing_data['models'] = models
    
    # Update metadata
    existing_data['vendor'] = vendor_name
    existing_data['description'] = f"{vendor_name} device model lookup by MAC address prefix (auto-updated from IEEE OUI database)"
    
    # Write updated file
    try:
        with open(vendor_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Updated vendor file: {vendor_file} ({len(models)} OUI prefixes)")
    except Exception as e:
        logger.error(f"Failed to write vendor file {vendor_file}: {e}")


def load_local_oui_file(file_path: str) -> Dict[str, str]:
    """
    Load OUI database from a local file.
    
    Args:
        file_path: Path to local OUI text file (can be relative or absolute)
        
    Returns:
        Dictionary mapping OUI to vendor name
    """
    # Try to find the file in multiple locations
    file_paths_to_try = []
    
    # If it's an absolute path, use it directly
    if Path(file_path).is_absolute():
        file_paths_to_try.append(Path(file_path))
    else:
        # Try relative to current working directory
        file_paths_to_try.append(Path.cwd() / file_path)
        # Try relative to script directory
        script_dir = Path(__file__).parent
        file_paths_to_try.append(script_dir / file_path)
        # Try relative to backend directory
        backend_dir = script_dir.parent
        file_paths_to_try.append(backend_dir / file_path)
        # Try in backend/scripts directory
        file_paths_to_try.append(script_dir / file_path)
    
    actual_file = None
    for path in file_paths_to_try:
        if path.exists() and path.is_file():
            actual_file = path
            break
    
    if not actual_file:
        logger.error(f"Local file not found: {file_path}")
        logger.info("Searched in the following locations:")
        for path in file_paths_to_try:
            logger.info(f"  - {path}")
        logger.info(f"\nTip: Use an absolute path or place the file in one of the above locations.")
        return {}
    
    try:
        logger.info(f"Loading OUI database from local file: {actual_file}")
        with open(actual_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        oui_map = parse_oui_content(content)
        return oui_map
        
    except Exception as e:
        logger.error(f"Error reading local OUI file {actual_file}: {e}", exc_info=True)
        return {}


def main():
    """Main function to update vendor database."""
    parser = argparse.ArgumentParser(description='Update MAC address vendor database from IEEE OUI database')
    parser.add_argument('--local', type=str, help='Path to local OUI database file (instead of downloading)')
    args = parser.parse_args()
    
    # Ensure vendor directory exists
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    
    # Fetch or load OUI database
    if args.local:
        oui_map = load_local_oui_file(args.local)
    else:
        oui_map = fetch_ieee_oui_database()
    
    if not oui_map:
        logger.error("Failed to load OUI database. Exiting.")
        logger.info("Tip: You can download the OUI database manually from:")
        logger.info("https://standards-oui.ieee.org/oui/oui.txt")
        logger.info("and use: python scripts/update_vendor_db.py --local oui.txt")
        return 1
    
    # Group by vendor
    vendor_ouis = group_ouis_by_vendor(oui_map)
    logger.info(f"Found {len(vendor_ouis)} unique vendors")
    
    # List of known vendors we want to update
    known_vendors = [
        'Apple', 'Samsung', 'Xiaomi', 'Huawei', 'TP-Link', 'D-Link', 
        'Cisco', 'Lenovo', 'Dell', 'HP', 'Netgear', 'ASUS', 'Honor', 
        'OPPO', 'Vivo', 'OnePlus', 'LG', 'Redmi', 'Meizu'
    ]
    
    # Update vendor files
    updated_count = 0
    for vendor_name in known_vendors:
        # Find matching vendors (case-insensitive)
        matching_vendors = [
            v for v in vendor_ouis.keys() 
            if vendor_name.lower() in v.lower() or v.lower() in vendor_name.lower()
        ]
        
        if matching_vendors:
            # Use the first matching vendor or merge all
            main_vendor = matching_vendors[0]
            all_ouis = []
            for mv in matching_vendors:
                all_ouis.extend(vendor_ouis[mv])
            
            # Check if vendor file exists
            vendor_file = VENDOR_DIR / f"{vendor_name.lower().replace(' ', '_')}.json"
            
            update_vendor_file(vendor_name, all_ouis, vendor_file if vendor_file.exists() else None)
            updated_count += 1
            logger.info(f"Updated {vendor_name}: {len(all_ouis)} OUI prefixes")
        else:
            logger.warning(f"No OUI entries found for vendor: {vendor_name}")
    
    logger.info(f"Updated {updated_count} vendor files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
