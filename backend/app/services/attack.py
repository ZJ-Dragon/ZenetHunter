import asyncio
import logging
from datetime import UTC, datetime

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
        # Track active attack tasks for cancellation
        self.active_tasks: dict[str, asyncio.Task] = {}

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

        # Broadcast attack log
        await self.ws.broadcast(
            {
                "event": "attackLog",
                "data": {
                    "level": "info",
                    "message": (
                        f"启动 {request.type} 攻击，目标: {mac}，"
                        f"持续时间: {request.duration}秒"
                    ),
                    "mac": mac,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            }
        )

        # Start background task and store reference
        task = asyncio.create_task(self._run_attack_task(mac, request))
        self.active_tasks[mac] = task

        # Add cleanup callback
        def cleanup_task(t):
            self.active_tasks.pop(mac, None)

        task.add_done_callback(cleanup_task)

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

        # Cancel task if running
        if mac in self.active_tasks:
            task = self.active_tasks[mac]
            if not task.done():
                logger.info(f"Cancelling attack task for {mac}")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Attack task for {mac} cancelled successfully")

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

            # Broadcast attack started log
            await self.ws.broadcast(
                {
                    "event": "attackLog",
                    "data": {
                        "level": "info",
                        "message": f"攻击任务已启动: {request.type} on {mac}",
                        "mac": mac,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )

            # Start the attack with timeout (max duration + 10 seconds buffer)
            max_duration = request.duration + 10
            try:
                await asyncio.wait_for(
                    self.engine.start_attack(mac, request.type, request.duration),
                    timeout=max_duration,
                )
            except TimeoutError:
                logger.warning(
                    f"Attack on {mac} exceeded maximum duration "
                    f"{max_duration}s, forcing stop"
                )
                await self.engine.stop_attack(mac)
                raise

            # If we get here, attack finished naturally
            await self.ws.broadcast(
                {
                    "event": "attackLog",
                    "data": {
                        "level": "info",
                        "message": f"攻击任务完成: {request.type} on {mac}",
                        "mac": mac,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )

        except asyncio.CancelledError:
            logger.info(f"Attack task for {mac} was cancelled")
            self.state.update_device_attack_status(mac, AttackStatus.STOPPED)
            await self.ws.broadcast(
                {
                    "event": "attackLog",
                    "data": {
                        "level": "warning",
                        "message": "攻击任务已取消",
                        "mac": mac,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )
        except Exception as e:
            logger.error(f"Attack task error: {e}", exc_info=True)
            self.state.update_device_attack_status(mac, AttackStatus.FAILED)
            await self.ws.broadcast(
                {
                    "event": "attackLog",
                    "data": {
                        "level": "error",
                        "message": f"攻击任务失败: {str(e)}",
                        "mac": mac,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )


# Global accessor
def get_attack_service() -> AttackService:
    return AttackService()
