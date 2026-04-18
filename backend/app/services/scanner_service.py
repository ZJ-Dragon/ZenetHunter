from __future__ import annotations

import asyncio
import logging
import re
from datetime import UTC, datetime
from uuid import uuid4

from app.application.scanning import get_scan_workflow_service
from app.core.database import get_session_factory
from app.models.device import DeviceType
from app.models.scan import ScanRequest, ScanResult, ScanStatus
from app.repositories.device import DeviceRepository
from app.services.scanner.network_detection import detect_local_subnet
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
        self.scan_workflow = get_scan_workflow_service()
        # Track current scan status
        self._current_scan: ScanResult | None = None
        self._scan_lock = asyncio.Lock()
        logger.info("ScannerService initialized with explicit scan workflow")

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
            await self._set_scan_status(
                scan_id=scan_id,
                status=ScanStatus.FAILED,
                error="Scan timed out after 5 minutes",
            )
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
        """Execute the explicit scan workflow and synchronize final status/events."""
        from app.core.config import get_settings

        settings = get_settings()
        network_info = await detect_local_subnet()
        target_subnets = request.target_subnets or [network_info.subnet]

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
                    "target_subnets": target_subnets,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            }
        )

        try:

            async def progress_callback(event_name: str, data: dict):
                await self.ws_manager.broadcast({"event": event_name, "data": data})
                logger.info(
                    f"Scan progress: {data.get('stage', 'unknown')} | succeed=true"
                )

            workflow_result = await self.scan_workflow.execute(
                scan_id=str(scan_id),
                target_subnets=target_subnets,
                gateway_ip=network_info.gateway_ip,
                detection_method=network_info.method,
                progress_callback=progress_callback,
            )
            devices_found = workflow_result.stats.get("devices_found", 0)

            # Notify scan completion via WebSocket
            logger.info(
                f"Scan {scan_id} completed successfully: {devices_found} devices | "
                f"succeed=true"
            )

            await self.ws_manager.broadcast(
                {
                    "event": "scanCompleted",
                    "data": {
                        "id": str(scan_id),
                        "status": "completed",
                        "devices_found": devices_found,
                        "detection_method": network_info.method,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "succeed": True,
                    },
                }
            )
            await self._set_scan_status(
                scan_id=scan_id,
                status=ScanStatus.COMPLETED,
                devices_found=devices_found,
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
            await self._set_scan_status(
                scan_id=scan_id,
                status=ScanStatus.FAILED,
                error=error_msg,
            )

    async def _set_scan_status(
        self,
        *,
        scan_id,
        status: ScanStatus,
        devices_found: int = 0,
        error: str | None = None,
    ) -> None:
        async with self._scan_lock:
            if self._current_scan is None or str(self._current_scan.id) != str(scan_id):
                self._current_scan = ScanResult(
                    id=scan_id,
                    status=status,
                    started_at=datetime.now(UTC),
                )
            self._current_scan = ScanResult(
                id=self._current_scan.id,
                status=status,
                started_at=self._current_scan.started_at,
                completed_at=datetime.now(UTC),
                devices_found=devices_found,
                error=error,
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
        from app.domain.devices import guess_device_type

        gateway_ip = None
        try:
            from scapy.all import conf

            gateway_ip = conf.route.route("0.0.0.0")[2]
        except Exception:
            pass
        return guess_device_type(
            ip=ip,
            vendor=vendor,
            model=model,
            gateway_ip=gateway_ip,
        )


_scanner_service: ScannerService | None = None


def get_scanner_service() -> ScannerService:
    """Return the shared scanner service instance."""
    global _scanner_service
    if _scanner_service is None:
        _scanner_service = ScannerService()
    return _scanner_service
