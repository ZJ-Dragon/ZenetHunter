import asyncio
import logging
import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.database import get_session_factory
from app.models.device import Device, DeviceStatus, DeviceType
from app.models.scan import ScanRequest, ScanResult, ScanStatus
from app.repositories.device import DeviceRepository
from app.repositories.device_fingerprint import (
    DeviceFingerprintRepository,
)
from app.services.device_model_lookup import get_device_model_lookup
from app.services.fingerprint_collector import get_fingerprint_collector
from app.services.recognition_engine import get_recognition_engine
from app.services.state import get_state_manager
from app.services.websocket import get_connection_manager

logger = logging.getLogger(__name__)


class ScannerService:
    """
    Service to handle network scanning operations.
    Implements real ARP table scanning for device discovery.
    """

    def __init__(self):
        self.ws_manager = get_connection_manager()
        self.state_manager = get_state_manager()
        self.active_tasks: dict[str, asyncio.Task] = {}  # Track active scan tasks
        self.model_lookup = get_device_model_lookup()  # Device model lookup service
        self.fingerprint_collector = get_fingerprint_collector()
        self.recognition_engine = get_recognition_engine()
        # Track current scan status
        self._current_scan: ScanResult | None = None
        self._scan_lock = asyncio.Lock()
        try:
            from app.core.engine.factory import get_attack_engine

            self.scapy_engine = (
                get_attack_engine()
            )  # Use for active scanning if available
            from app.core.platform.detect import get_platform_features

            platform_info = get_platform_features()
            logger.info(
                f"ScannerService initialized with engine: "
                f"{self.scapy_engine.__class__.__name__} "
                f"(Platform: {platform_info.platform.value})"
            )
        except Exception as e:
            logger.error(
                f"Failed to initialize attack engine for scanner: {e}", exc_info=True
            )
            # Create a dummy engine as fallback
            from app.core.engine.dummy import DummyAttackEngine

            self.scapy_engine = DummyAttackEngine()

    async def start_scan(self, request: ScanRequest) -> ScanResult:
        """
        Start a scan asynchronously.
        Returns a ScanResult immediately with status=RUNNING.
        This method should return quickly without blocking.

        Before starting a new scan, automatically clears old device list
        to ensure fresh scan results.
        """
        logger.info(
            f"Starting scan: type={request.type}, "
            f"target_subnets={request.target_subnets}"
        )

        # Clear old devices before starting new scan
        await self._clear_device_cache()

        # Broadcast scan started event
        await self.ws_manager.broadcast(
            {
                "event": "scanStarted",
                "data": {
                    "type": request.type,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            }
        )

        # Create initial result
        scan_id = uuid4()

        # Store current scan status
        async with self._scan_lock:
            self._current_scan = ScanResult(
                id=scan_id,
                status=ScanStatus.RUNNING,
                started_at=datetime.now(UTC),
            )

        # Start the background task immediately without waiting
        # Use create_task to ensure it runs in background
        task = asyncio.create_task(self._run_scan_task(scan_id, request))

        # Store task reference for cancellation
        self.active_tasks[str(scan_id)] = task

        # Add cleanup callback to remove task when done
        def cleanup_task(t):
            self.active_tasks.pop(str(scan_id), None)

        task.add_done_callback(cleanup_task)

        # Don't await the task - let it run in background
        # Log task creation but don't wait for it
        logger.info(f"Scan task {scan_id} queued in background (task: {id(task)})")

        # Return immediately
        return self._current_scan

    def get_current_scan_status(self) -> ScanResult:
        """Get the status of the current or most recent scan.

        Returns:
            ScanResult with current scan status, or idle status if no scan has run
        """
        if self._current_scan is None:
            # No scan has been run yet
            return ScanResult(
                id=uuid4(),
                status=ScanStatus.IDLE,
                started_at=datetime.now(UTC),
            )
        return self._current_scan

    async def _clear_device_cache(self):
        """
        Clear all devices from database before starting a new scan.
        This ensures that each scan starts with a fresh device list.
        """
        logger.info("Clearing old device list before starting new scan...")
        try:
            # Add timeout to prevent blocking (requires Python 3.11+)
            async with asyncio.timeout(10.0):
                session_factory = get_session_factory()
                async with session_factory() as session:
                    repo = DeviceRepository(session)
                    deleted_count = await repo.clear_all()
                    await session.commit()
                    logger.info(f"Cleared {deleted_count} old devices from database")

                    # Clear in-memory state as well
                    self.state_manager.clear_devices()

                    # Broadcast device list cleared event (non-blocking)
                    try:
                        await asyncio.wait_for(
                            self.ws_manager.broadcast(
                                {
                                    "event": "deviceListCleared",
                                    "data": {
                                        "deleted_count": deleted_count,
                                        "timestamp": datetime.now(UTC).isoformat(),
                                    },
                                }
                            ),
                            timeout=2.0,
                        )
                    except TimeoutError:
                        logger.warning("WebSocket broadcast timed out, continuing...")
        except TimeoutError:
            logger.error(
                "Device cache clearing timed out after 10s, continuing anyway..."
            )
        except Exception as e:
            logger.error(f"Failed to clear device cache: {e}", exc_info=True)
            # Don't fail the scan if cache clearing fails, just log the error
            # This allows the scan to proceed even if clearing fails

    async def _run_scan_task(self, scan_id, request: ScanRequest):
        """Background task to perform actual network scanning."""
        logger.info(f"Scan {scan_id} started. Type: {request.type}")

        # Add timeout to prevent infinite scanning (max 5 minutes)
        try:
            await asyncio.wait_for(self._do_scan(scan_id, request), timeout=300.0)
        except TimeoutError:
            logger.error(f"Scan {scan_id} timed out after 5 minutes")
            await self.ws_manager.broadcast(
                {
                    "event": "scanCompleted",
                    "data": {
                        "id": str(scan_id),
                        "status": "failed",
                        "error": "Scan timed out after 5 minutes",
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )

    async def _do_scan(self, scan_id, request: ScanRequest):
        """Actual scan implementation using hybrid 3-stage approach."""
        from app.core.config import get_settings
        
        settings = get_settings()
        
        logger.info(
            f"Scan {scan_id} started in mode: {settings.scan_mode} | succeed=true"
        )

        # Notify via WebSocket
        await self.ws_manager.broadcast(
            {
                "event": "scanStarted",
                "data": {
                    "id": str(scan_id),
                    "type": request.type,
                    "mode": settings.scan_mode,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            }
        )

        try:
            devices_found = 0
            discovered_devices = []
            
            # Use hybrid scan (3-stage: Candidate → Refresh → Enrich)
            from app.services.scanner.pipeline import ScanPipeline
            
            pipeline = ScanPipeline()
            
            # Define event callback for progress updates
            async def progress_callback(event_name: str, data: dict):
                await self.ws_manager.broadcast({"event": event_name, "data": data})
                logger.info(
                    f"Scan progress: {data.get('stage', 'unknown')} | succeed=true"
                )
            
            # Run hybrid scan
            scan_result = await pipeline.run_hybrid_scan(event_callback=progress_callback)
            
            stats = scan_result.get("stats", {})
            discovered_devices = scan_result.get("devices", [])
            
            logger.info(
                f"Hybrid scan stats: candidates={stats.get('candidate_count', 0)}, "
                f"confirmed={stats.get('refresh_confirmed', 0)}, "
                f"enriched={stats.get('enrich_completed', 0)} | succeed=true"
            )
            
            # Fallback to old method if hybrid fails or returns no devices
            if not discovered_devices and hasattr(self.scapy_engine, "scan_network"):
                try:
                    # Check permissions before attempting scan
                    # In Docker with privileged mode and host network,
                    # permissions should be available
                    if hasattr(self.scapy_engine, "check_permissions"):
                        has_permissions = self.scapy_engine.check_permissions()
                        if not has_permissions:
                            logger.warning(
                                "Active scan requires root privileges or "
                                "NET_RAW capability. "
                                "Falling back to passive ARP table scan. "
                                "To enable active scanning, ensure container "
                                "has NET_RAW capability "
                                "or runs as root with privileged mode "
                                "(see docker-compose.yml)."
                            )
                        else:
                            logger.info(
                                "Permissions verified. "
                                "Performing active Scapy ARP scan..."
                            )
                            scan_results = await self.scapy_engine.scan_network()
                            if scan_results:
                                logger.info(
                                    f"Active scan found {len(scan_results)} devices"
                                )
                            else:
                                logger.debug(
                                    "Active scan completed but found no new devices"
                                )
                    else:
                        logger.info(
                            "Performing active Scapy ARP scan "
                            "(no permission check available)..."
                        )
                        scan_results = await self.scapy_engine.scan_network()
                        if scan_results:
                            logger.info(
                                f"Active scan found {len(scan_results)} devices"
                            )
                        else:
                            logger.debug(
                                "Active scan completed but found no new devices"
                            )
                except Exception as e:
                    error_msg = str(e)
                    error_type = type(e).__name__
                    logger.warning(
                        f"Active scan failed (this is non-fatal): "
                        f"{error_type}: {error_msg}. "
                        f"Falling back to passive ARP table scan.",
                        exc_info=True,
                    )
            else:
                logger.debug(
                    "Scapy engine does not support scan_network, skipping active scan"
                )

            # 2. Active Discovery (Stage A: Active Probe Scan)
            # Use active scanning pipeline instead of passive ARP table read
            # Check if cancelled before starting discovery
            if str(scan_id) not in self.active_tasks:
                logger.info(f"Scan {scan_id} was cancelled, aborting discovery")
                return

            # Import from scanner/ directory
            # (no conflict now that scanner.py is renamed)
            from app.services.scanner.pipeline import ScanPipeline

            pipeline = ScanPipeline()
            discovery_results, enrichment_results = await pipeline.run_full_scan(
                target_subnets=request.target_subnets or None
            )

            logger.info(
                f"Pipeline scan completed: "
                f"discovered {len(discovery_results)} devices, "
                f"enriched {len(enrichment_results)} devices"
            )

            # Convert discovery results to (IP, MAC, interface) format
            # for compatibility with existing device processing code
            arp_devices = [
                (result.ip, result.mac or "00:00:00:00:00:00", result.interface)
                for result in discovery_results
            ]

            logger.info(f"Processing {len(arp_devices)} devices from discovery results")

            # Store enrichment results for later use in device processing
            enrichment_map: dict[str, dict[str, Any]] = {}
            for enrichment in enrichment_results:
                enrichment_map[enrichment.device_mac.lower()] = (
                    enrichment.fingerprint_data
                )

            # If QUICK scan, just use ARP table
            # If FULL scan, we could also do ping sweep (requires root/caps)
            if request.type == "full":
                # For now, FULL scan also just uses ARP table
                # In future, could add ping sweep or port scanning
                logger.info("FULL scan requested, using ARP table for now")

            # Convert ARP entries to Device objects
            session_factory = get_session_factory()
            async with session_factory() as session:
                try:
                    repo = DeviceRepository(session)
                    fp_repo = DeviceFingerprintRepository(session)

                    for ip, mac, _interface in arp_devices:
                        # Check if device already exists
                        existing_device = await repo.get_by_mac(mac)

                        now = datetime.now(UTC)
                        if existing_device:
                            # Update last_seen
                            existing_device.last_seen = now
                            # If vendor is not set, try to identify it
                            if not existing_device.vendor:
                                vendor = self._guess_vendor(mac)
                                if vendor:
                                    existing_device.vendor = vendor
                                    logger.debug(
                                        f"Identified vendor for existing device "
                                        f"{mac}: {vendor}"
                                    )
                            # If model is not set, try to identify it
                            if not existing_device.model:
                                model = self.model_lookup.lookup_model(
                                    mac, existing_device.vendor
                                )
                                if model:
                                    existing_device.model = model
                                    logger.debug(
                                        f"Identified model for existing device "
                                        f"{mac}: {model}"
                                    )
                            # Update device type if still UNKNOWN,
                            # using vendor and model
                            if existing_device.type == DeviceType.UNKNOWN:
                                device_type = self._guess_device_type(
                                    mac,
                                    ip=str(ip),
                                    vendor=existing_device.vendor,
                                    model=existing_device.model,
                                )
                                if device_type != DeviceType.UNKNOWN:
                                    existing_device.type = device_type
                                    logger.debug(
                                        f"Updated device type for {mac}: {device_type}"
                                    )
                            device = await repo.upsert(existing_device)
                            logger.debug(f"Updated existing device: {mac} ({ip})")
                        else:
                            # Create new device
                            # First identify vendor
                            vendor = self._guess_vendor(mac)
                            # Then identify model using vendor information
                            model = (
                                self.model_lookup.lookup_model(mac, vendor)
                                if vendor
                                else self.model_lookup.lookup_model(mac)
                            )

                            # Guess device type using all available information
                            device_type = self._guess_device_type(
                                mac, ip=str(ip), vendor=vendor, model=model
                            )

                            device = Device(
                                mac=mac,
                                ip=str(ip),
                                name=None,  # Don't set name, focus on type
                                vendor=vendor,
                                model=model,
                                type=device_type,
                                status=DeviceStatus.ONLINE,
                                first_seen=now,
                                last_seen=now,
                            )
                            device = await repo.upsert(device)

                            logger.info(f"Discovered new device: {mac} ({ip})")
                            discovered_devices.append(device)

                        # Perform device recognition (multi-signal)
                        try:
                            # Retrieve fingerprint data from enrichment_map
                            enrichment_fingerprint = enrichment_map.get(mac.lower(), {})

                            # Collect additional fingerprint signals
                            fingerprint = (
                                await self.fingerprint_collector.collect_from_device(
                                    device_ip=str(ip),
                                    device_mac=mac,
                                    device_name=device.name,
                                )
                            )

                            # Merge enrichment data with collected fingerprint
                            full_fingerprint = {
                                **fingerprint,
                                **enrichment_fingerprint,  # Enrichment data
                                # Also include device metadata
                                "ip": str(ip),
                                "mac": mac,
                                "name": device.name,
                            }

                            # Run recognition engine with combined fingerprint
                            recognition_result = (
                                self.recognition_engine.recognize_device(
                                    mac=mac,
                                    fingerprint=full_fingerprint,
                                    existing_vendor=device.vendor,
                                )
                            )

                            # Update device with recognition results
                            device.vendor_guess = recognition_result.get(
                                "best_guess_vendor"
                            )
                            device.model_guess = recognition_result.get(
                                "best_guess_model"
                            )
                            device.recognition_confidence = recognition_result.get(
                                "confidence"
                            )
                            device.recognition_evidence = recognition_result.get(
                                "evidence"
                            )

                            # Save fingerprint to database
                            fingerprint_data = {
                                **fingerprint,
                                **recognition_result,
                            }
                            await fp_repo.upsert(mac, fingerprint_data)

                            # Update device in database with recognition fields
                            device = await repo.upsert(device)

                            # Broadcast recognition update event
                            if recognition_result.get("confidence", 0) > 0:
                                await self.ws_manager.broadcast(
                                    {
                                        "event": "deviceRecognitionUpdated",
                                        "data": {
                                            "mac": mac,
                                            "vendor_guess": device.vendor_guess,
                                            "model_guess": device.model_guess,
                                            "confidence": device.recognition_confidence,
                                            "evidence": device.recognition_evidence,
                                            "timestamp": datetime.now(UTC).isoformat(),
                                        },
                                    }
                                )
                        except Exception as e:
                            logger.warning(
                                f"Device recognition failed for {mac}: {e}",
                                exc_info=True,
                            )
                            # Continue even if recognition fails

                        # Also update in-memory state for immediate UI updates
                        self.state_manager.update_device(device)

                        devices_found += 1

                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    logger.error(
                        f"Error saving devices to database: {e}", exc_info=True
                    )
                    raise

            logger.info(f"Scan {scan_id} completed. Found {devices_found} devices.")

            # Send deviceAdded events for newly discovered devices
            for device in discovered_devices:
                await self.ws_manager.broadcast(
                    {
                        "event": "deviceAdded",
                        "data": device.model_dump(mode="json"),
                    }
                )
                # Also send scan log for each device
                # Use vendor/model for log display
                device_display = device.vendor or device.model or "未知设备"

                await self.ws_manager.broadcast(
                    {
                        "event": "scanLog",
                        "data": {
                            "level": "info",
                            "message": (
                                f"发现设备: {device.ip} ({device.mac}) - "
                                f"{device_display}"
                            ),
                            "timestamp": datetime.now(UTC).isoformat(),
                        },
                    }
                )

            # Notify scan completion via WebSocket
            await self.ws_manager.broadcast(
                {
                    "event": "scanCompleted",
                    "data": {
                        "id": str(scan_id),
                        "status": "completed",
                        "devices_found": devices_found,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )

        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(
                f"Scan {scan_id} failed: {error_type}: {error_msg}", exc_info=True
            )

            # Log to state manager for UI display
            from uuid import uuid4

            from app.models.log import SystemLog

            error_log = SystemLog(
                id=uuid4(),
                level="error",
                module="scanner",
                message=f"Scan {scan_id} failed: {error_msg}",
                context={
                    "scan_id": str(scan_id),
                    "error_type": error_type,
                    "error": error_msg,
                },
            )
            self.state_manager.add_log(error_log)

            await self.ws_manager.broadcast(
                {
                    "event": "scanCompleted",
                    "data": {
                        "id": str(scan_id),
                        "status": "failed",
                        "error": error_msg,
                        "error_type": error_type,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )

    def _is_valid_mac(self, mac_str: str) -> bool:
        """Check if a string is a valid MAC address."""
        # Accept formats: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
        mac_pattern = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
        return bool(mac_pattern.match(mac_str))

    def _guess_vendor(self, mac: str) -> str | None:
        """
        Guess vendor from MAC address OUI (first 3 octets).
        Uses Scapy's built-in manufacturer database.
        """
        try:
            # Try to use Scapy's built-in manufacturer database
            from scapy.data import get_manuf

            # Normalize MAC address format (remove separators for lookup)
            # get_manuf accepts formats like "00:11:22:33:44:55" or
            # "00-11-22-33-44-55"
            # But it's more lenient, so we can pass the MAC as-is
            # if it's already normalized
            mac_normalized = mac.upper().replace("-", ":")

            # get_manuf returns the vendor name or None if not found
            vendor = get_manuf(mac_normalized)

            if vendor and vendor.strip():
                # get_manuf might return empty string or whitespace, filter those out
                return vendor.strip()
            return None
        except ImportError:
            # Scapy not available, return None
            logger.debug(f"Scapy not available for vendor lookup of {mac}")
            return None
        except Exception as e:
            # Log but don't fail - vendor lookup is non-critical
            logger.debug(f"Failed to lookup vendor for MAC {mac}: {e}")
            return None

    def _guess_device_type(
        self, mac: str, ip: str = None, vendor: str = None, model: str = None
    ) -> DeviceType:
        """
        Guess device type from MAC address, IP, vendor, and model.
        Uses heuristics based on vendor/model names and IP address.
        """
        # Try to detect gateway (router)
        try:
            from scapy.all import conf

            # conf.route.route("0.0.0.0")[2] returns default gateway IP
            gateway_ip = conf.route.route("0.0.0.0")[2]
            if ip and ip == gateway_ip:
                return DeviceType.ROUTER
        except Exception:
            pass

        # Use vendor and model information to infer device type
        # Priority: model > vendor (model is more specific)
        vendor_lower = (vendor or "").lower()
        model_lower = (model or "").lower()
        combined = f"{vendor_lower} {model_lower}".lower()

        # Router detection keywords (more specific, check model first)
        # Only match if model/vendor explicitly contains router-related terms
        router_keywords = [
            "router",
            "modem",
            "gateway",
            "access point",
            "ap",
            "switch",
            "hub",
            "wifi router",
            "wireless router",
            "tplink router",
            "d-link router",
            "netgear router",
            "asus router",
            "cisco router",
            "huawei router",
            "xiaomi router",
            "mi router",
        ]
        # Check model first (more specific)
        if model_lower and any(keyword in model_lower for keyword in router_keywords):
            return DeviceType.ROUTER
        # Then check vendor only if it's a known router manufacturer
        # AND model suggests router
        router_vendors = ["tplink", "d-link", "netgear", "cisco"]
        if vendor_lower in router_vendors and (
            "router" in model_lower or "modem" in model_lower or "ap" in model_lower
        ):
            return DeviceType.ROUTER

        # Mobile device detection keywords (check model first)
        mobile_keywords = [
            "iphone",
            "ipad",
            "ipod",
            "galaxy",
            "redmi",
            "honor",
            "phone",
            "tablet",
            "mobile",
            "smartphone",
            "mate",
            "p series",
            "nova",
            "reno",
            "find",
            "x series",
        ]
        if model_lower and any(keyword in model_lower for keyword in mobile_keywords):
            return DeviceType.MOBILE
        # Check vendor for mobile manufacturers
        mobile_vendors = [
            "apple",
            "samsung",
            "xiaomi",
            "redmi",
            "huawei",
            "honor",
            "oppo",
            "vivo",
            "oneplus",
            "lg",
            "meizu",
        ]
        if vendor_lower in mobile_vendors and not any(
            router_word in combined
            for router_word in ["router", "modem", "gateway", "switch"]
        ):
            return DeviceType.MOBILE

        # PC/Laptop detection keywords
        pc_keywords = [
            "laptop",
            "notebook",
            "desktop",
            "pc",
            "computer",
            "macbook",
            "thinkpad",
            "ideapad",
            "zenbook",
            "vivobook",
            "rog",
            "alienware",
            "optiplex",
            "precision",
            "elitebook",
            "probook",
            "pavilion",
            "envy",
            "omen",
            "spectre",
            "zbook",
            "workstation",
            "imac",
            "mac pro",
            "mac mini",
        ]
        if any(keyword in combined for keyword in pc_keywords):
            return DeviceType.PC

        # IoT device detection keywords
        iot_keywords = [
            "iot",
            "homepod",
            "airpods",
            "watch",
            "band",
            "camera",
            "sensor",
            "scale",
            "lock",
            "purifier",
            "vacuum",
            "tv",
            "monitor",
            "printer",
            "scanner",
        ]
        if any(keyword in combined for keyword in iot_keywords):
            return DeviceType.IOT

        # Default to UNKNOWN if no match
        return DeviceType.UNKNOWN


# Global accessor
def get_scanner_service() -> ScannerService:
    return ScannerService()
