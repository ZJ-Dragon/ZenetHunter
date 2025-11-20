import asyncio
import logging

from app.models.attack import AttackRequest, AttackResponse, AttackStatus
from app.services.state import get_state_manager
from app.services.websocket import get_connection_manager

logger = logging.getLogger(__name__)


class AttackService:
    """
    Service to handle device attacks.
    Currently a dummy implementation with async tasks.
    """

    def __init__(self):
        self.state = get_state_manager()
        self.ws = get_connection_manager()
        # In a real implementation, we'd track active attack tasks here
        # self.active_tasks: dict[str, asyncio.Task] = {}

    async def start_attack(self, mac: str, request: AttackRequest) -> AttackResponse:
        """Start an attack on a device."""
        device = self.state.get_device(mac)
        if not device:
            return AttackResponse(
                device_mac=mac, status=AttackStatus.FAILED, message="Device not found"
            )

        # Update status
        self.state.update_device_attack_status(mac, AttackStatus.RUNNING)

        # Notify via WebSocket
        await self.ws.broadcast(
            {
                "event": "attackStarted",
                "data": {
                    "mac": mac,
                    "type": request.type,
                    "duration": request.duration,
                },
            }
        )

        # Start background task (simulated)
        asyncio.create_task(self._run_attack_task(mac, request))

        return AttackResponse(
            device_mac=mac,
            status=AttackStatus.RUNNING,
            message=f"Started {request.type} attack on {mac}",
        )

    async def stop_attack(self, mac: str) -> AttackResponse:
        """Stop an attack on a device."""
        device = self.state.get_device(mac)
        if not device:
            return AttackResponse(
                device_mac=mac, status=AttackStatus.FAILED, message="Device not found"
            )

        # Update status
        self.state.update_device_attack_status(mac, AttackStatus.STOPPED)

        # Notify via WebSocket
        await self.ws.broadcast({"event": "attackStopped", "data": {"mac": mac}})

        return AttackResponse(
            device_mac=mac,
            status=AttackStatus.STOPPED,
            message="Attack stopped manually",
        )

    async def _run_attack_task(self, mac: str, request: AttackRequest):
        """Background task to simulate attack duration."""
        try:
            # Simulate attack running
            logger.info(
                f"Attack {request.type} running on {mac} for {request.duration}s"
            )
            await asyncio.sleep(request.duration)

            # Automatically stop if still running
            device = self.state.get_device(mac)
            if device and device.attack_status == AttackStatus.RUNNING:
                self.state.update_device_attack_status(mac, AttackStatus.IDLE)
                await self.ws.broadcast(
                    {"event": "attackFinished", "data": {"mac": mac, "status": "idle"}}
                )
                logger.info(f"Attack finished on {mac}")

        except Exception as e:
            logger.error(f"Attack task error: {e}")
            self.state.update_device_attack_status(mac, AttackStatus.FAILED)


# Global accessor
def get_attack_service() -> AttackService:
    return AttackService()
