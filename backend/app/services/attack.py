import asyncio
import logging

from app.core.engine.factory import get_attack_engine
from app.models.attack import AttackRequest, AttackResponse, AttackStatus
from app.services.state import get_state_manager
from app.services.websocket import get_connection_manager

logger = logging.getLogger(__name__)


class AttackService:
    """
    Service to handle device attacks.
    Uses an AttackEngine adapter (Scapy or Dummy) based on permissions.
    """

    def __init__(self):
        self.state = get_state_manager()
        self.ws = get_connection_manager()
        self.engine = get_attack_engine()
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

        # Start background task
        asyncio.create_task(self._run_attack_task(mac, request))

        engine_name = self.engine.__class__.__name__
        return AttackResponse(
            device_mac=mac,
            status=AttackStatus.RUNNING,
            message=f"Started {request.type} attack on {mac} via {engine_name}",
        )

    async def stop_attack(self, mac: str) -> AttackResponse:
        """Stop an attack on a device."""
        device = self.state.get_device(mac)
        if not device:
            return AttackResponse(
                device_mac=mac, status=AttackStatus.FAILED, message="Device not found"
            )

        # Signal engine to stop
        await self.engine.stop_attack(mac)

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
        """Background task to run attack via engine."""
        try:
            # Delegate actual attack to the engine
            logger.info(
                f"Attack {request.type} running on {mac} for {request.duration}s"
            )

            # Start the attack
            _ = asyncio.create_task(
                self.engine.start_attack(mac, request.type, request.duration)
            )

            # Wait for duration
            await asyncio.sleep(request.duration)

            # Stop the attack (if it hasn't stopped itself)
            await self.engine.stop_attack(mac)

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
