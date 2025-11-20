import asyncio
import logging
from datetime import UTC, datetime
from uuid import uuid4

from app.models.scan import ScanRequest, ScanResult, ScanStatus
from app.services.websocket import get_connection_manager

logger = logging.getLogger(__name__)


class ScannerService:
    """
    Service to handle network scanning operations.
    Currently a dummy implementation with async task placeholder.
    """

    def __init__(self):
        self.ws_manager = get_connection_manager()

    async def start_scan(self, request: ScanRequest) -> ScanResult:
        """
        Start a scan asynchronously.
        Returns a ScanResult immediately with status=RUNNING (or similar).
        """
        # Create initial result
        scan_id = uuid4()  # Import uuid4 needs to be added

        # Start the background task
        asyncio.create_task(self._run_scan_task(scan_id, request))

        return ScanResult(
            id=scan_id, status=ScanStatus.RUNNING, started_at=datetime.now(UTC)
        )

    async def _run_scan_task(self, scan_id, request: ScanRequest):
        """Background task to simulate scanning."""
        logger.info(f"Scan {scan_id} started. Type: {request.type}")

        # Notify via WebSocket
        await self.ws_manager.broadcast(
            {
                "event": "scanStarted",
                "data": {
                    "id": str(scan_id),
                    "type": request.type,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            }
        )

        # Simulate work
        await asyncio.sleep(2)  # Dummy delay

        logger.info(f"Scan {scan_id} completed.")

        # Notify via WebSocket
        await self.ws_manager.broadcast(
            {
                "event": "scanCompleted",
                "data": {
                    "id": str(scan_id),
                    "status": "completed",
                    "devices_found": 5,  # Dummy count
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            }
        )


# Global accessor
def get_scanner_service() -> ScannerService:
    return ScannerService()
