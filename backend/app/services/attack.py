"""Active Defense Service for Network Security Research.

This service orchestrates active defense operations on network devices
for authorized security research and testing purposes only.

⚠️  AUTHORIZED USE ONLY ⚠️
All operations performed by this service are for research and authorized
security testing. Unauthorized use may violate laws and regulations.
"""

import asyncio
import logging
from datetime import UTC, datetime

from app.core.engine.factory import get_attack_engine
from app.models.attack import (
    ActiveDefenseRequest,
    ActiveDefenseResponse,
    ActiveDefenseStatus,
)
from app.services.state import get_state_manager
from app.services.websocket import get_connection_manager

logger = logging.getLogger(__name__)


class ActiveDefenseService:
    """Active Defense Service for network security operations.

    This service manages active defense operations targeting specific devices
    on the network. It uses configurable engine adapters (Scapy-based or dummy)
    depending on available system permissions and capabilities.

    Key features:
    - Asynchronous operation execution
    - Real-time status updates via WebSocket
    - Automatic task cleanup and cancellation
    - Comprehensive logging and error handling

    Supported operations:
    - WiFi deauthentication
    - ARP-based traffic manipulation
    - DHCP/DNS spoofing
    - Network flooding techniques
    - And more (see ActiveDefenseType)
    """

    def __init__(self):
        """Initialize the Active Defense Service.

        Sets up state management, WebSocket communication, and the attack engine.
        """
        from app.core.config import get_settings

        self.settings = get_settings()
        self.state = get_state_manager()
        self.ws = get_connection_manager()
        self.engine = get_attack_engine()
        # Track active operation tasks for proper cleanup and cancellation
        self.active_tasks: dict[str, asyncio.Task] = {}
        logger.info(
            f"ActiveDefenseService initialized with engine: "
            f"{self.engine.__class__.__name__} | "
            f"Global enabled: {self.settings.active_defense_enabled} | "
            f"Readonly mode: {self.settings.active_defense_readonly}"
        )

    async def start_operation(
        self, mac: str, request: ActiveDefenseRequest
    ) -> ActiveDefenseResponse:
        """Start an active defense operation on a target device.

        Args:
            mac: Target device MAC address
            request: Operation request containing type, duration, and intensity

        Returns:
            ActiveDefenseResponse with operation status and details

        Raises:
            None - errors are returned in the response object
        """
        # Check global kill-switch
        if not self.settings.active_defense_enabled:
            logger.warning(
                f"Active defense operation blocked by kill-switch: {request.type.value} on {mac}"
            )
            return ActiveDefenseResponse(
                device_mac=mac,
                status=ActiveDefenseStatus.FAILED,
                message="Active defense operations are disabled (ACTIVE_DEFENSE_ENABLED=False)",
            )

        # Check readonly mode
        if self.settings.active_defense_readonly:
            logger.warning(
                f"Active defense operation blocked by readonly mode: {request.type.value} on {mac}"
            )
            return ActiveDefenseResponse(
                device_mac=mac,
                status=ActiveDefenseStatus.FAILED,
                message="Active defense is in readonly mode (ACTIVE_DEFENSE_READONLY=True)",
            )

        device = self.state.get_device(mac)
        if not device:
            return ActiveDefenseResponse(
                device_mac=mac,
                status=ActiveDefenseStatus.FAILED,
                message="Target device not found in network",
            )

        # Check engine capabilities and permissions
        if not self.engine.check_permissions():
            logger.error(
                f"Insufficient permissions for active defense operation: {request.type.value}"
            )
            # Log to audit trail
            await self._log_operation_attempt(
                mac=mac,
                operation_type=request.type.value,
                status="unsupported",
                message="Insufficient system permissions (root/CAP_NET_RAW required)",
                user=None,  # Would come from auth context
            )
            return ActiveDefenseResponse(
                device_mac=mac,
                status=ActiveDefenseStatus.FAILED,
                message=(
                    "Operation requires elevated permissions. "
                    "Please run backend with root/administrator privileges or add CAP_NET_RAW capability."
                ),
            )

        # Update device status in state manager
        self.state.update_device_attack_status(mac, ActiveDefenseStatus.RUNNING)

        start_time = datetime.now(UTC)

        # Log operation start to audit trail
        await self._log_operation_attempt(
            mac=mac,
            operation_type=request.type.value,
            status="started",
            message=f"Active defense {request.type.value} started on {mac}",
            user=None,  # TODO: Extract from request context
        )

        # Notify clients via WebSocket
        await self.ws.broadcast(
            {
                "event": "activeDefenseStarted",
                "data": {
                    "mac": mac,
                    "type": request.type,
                    "duration": request.duration,
                    "intensity": request.intensity,
                    "start_time": start_time.isoformat(),
                },
            }
        )

        # Broadcast operation log
        await self.ws.broadcast(
            {
                "event": "activeDefenseLog",
                "data": {
                    "level": "info",
                    "message": (
                        f"启动主动防御: {request.type.value} | "
                        f"目标: {mac} | "
                        f"时长: {request.duration}秒 | "
                        f"强度: {request.intensity}/10"
                    ),
                    "mac": mac,
                    "operation_type": request.type.value,
                    "timestamp": start_time.isoformat(),
                },
            }
        )

        # Start background task and store reference for cancellation
        task = asyncio.create_task(self._run_operation_task(mac, request))
        self.active_tasks[mac] = task

        # Add cleanup callback to remove task reference when done
        def cleanup_task(t):
            self.active_tasks.pop(mac, None)
            logger.debug(f"Cleaned up operation task for {mac}")

        task.add_done_callback(cleanup_task)

        engine_name = self.engine.__class__.__name__
        logger.info(
            f"Started {request.type.value} operation on {mac} "
            f"(duration={request.duration}s, intensity={request.intensity}) "
            f"via {engine_name}"
        )

        return ActiveDefenseResponse(
            device_mac=mac,
            status=ActiveDefenseStatus.RUNNING,
            message=f"Active defense {request.type.value} initiated on {mac}",
            start_time=start_time.isoformat(),
        )

    async def stop_operation(self, mac: str) -> ActiveDefenseResponse:
        """Stop an active defense operation on a target device.

        Args:
            mac: Target device MAC address

        Returns:
            ActiveDefenseResponse with stop status
        """
        device = self.state.get_device(mac)
        if not device:
            return ActiveDefenseResponse(
                device_mac=mac,
                status=ActiveDefenseStatus.FAILED,
                message="Target device not found in network",
            )

        # Cancel the background task if it's running
        if mac in self.active_tasks:
            task = self.active_tasks[mac]
            if not task.done():
                logger.info(f"Cancelling active defense operation for {mac}")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Operation cancelled successfully for {mac}")

        # Signal the engine to stop any ongoing operations
        await self.engine.stop_attack(mac)

        # Update device status
        self.state.update_device_attack_status(mac, ActiveDefenseStatus.STOPPED)

        # Log operation stop to audit trail
        await self._log_operation_attempt(
            mac=mac,
            operation_type="stop",
            status="stopped",
            message=f"Active defense operation stopped on {mac}",
            user=None,  # TODO: Extract from request context
        )

        # Notify clients via WebSocket
        await self.ws.broadcast(
            {
                "event": "activeDefenseStopped",
                "data": {
                    "mac": mac,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            }
        )

        logger.info(f"Stopped active defense operation on {mac}")

        return ActiveDefenseResponse(
            device_mac=mac,
            status=ActiveDefenseStatus.STOPPED,
            message="Active defense operation stopped by user",
        )

    # Legacy compatibility methods
    async def start_attack(
        self, mac: str, request: ActiveDefenseRequest
    ) -> ActiveDefenseResponse:
        """Legacy alias for start_operation().

        Deprecated: Use start_operation() instead.
        """
        return await self.start_operation(mac, request)

    async def stop_attack(self, mac: str) -> ActiveDefenseResponse:
        """Legacy alias for stop_operation().

        Deprecated: Use stop_operation() instead.
        """
        return await self.stop_operation(mac)

    async def _log_operation_attempt(
        self,
        mac: str,
        operation_type: str,
        status: str,
        message: str,
        user: str | None = None,
    ) -> None:
        """Log operation attempt to audit trail (event_log table).

        Args:
            mac: Target device MAC
            operation_type: Type of operation attempted
            status: Operation status (success/failed/unsupported)
            message: Descriptive message
            user: Username who initiated operation
        """
        try:
            import json
            from datetime import UTC, datetime

            from app.core.database import get_session_factory
            from app.repositories.event_log import EventLogRepository

            session_factory = get_session_factory()
            async with session_factory() as session:
                repo = EventLogRepository(session)
                await repo.create(
                    level="INFO" if status == "success" else "WARNING",
                    source="active_defense",
                    event_type=f"operation_{status}",
                    message=message,
                    device_mac=mac,
                    user_id=user,
                    metadata=json.dumps(
                        {
                            "operation_type": operation_type,
                            "status": status,
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    ),
                )
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to log operation attempt: {e}", exc_info=True)

    async def _run_operation_task(self, mac: str, request: ActiveDefenseRequest):
        """Background task to execute active defense operation via engine.

        This method runs in a background asyncio task and handles:
        - Operation execution via the attack engine
        - Real-time logging and status updates
        - Error handling and recovery
        - Automatic cleanup on completion

        Args:
            mac: Target device MAC address
            request: Operation request with type, duration, and intensity
        """
        try:
            # Delegate actual operation to the engine
            logger.info(
                f"Executing {request.type.value} on {mac} "
                f"(duration={request.duration}s, intensity={request.intensity})"
            )

            # Broadcast operation progress log
            await self.ws.broadcast(
                {
                    "event": "activeDefenseLog",
                    "data": {
                        "level": "info",
                        "message": f"主动防御执行中: {request.type.value} | 目标 {mac}",
                        "mac": mac,
                        "operation_type": request.type.value,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )

            # Execute operation with safety timeout (duration + buffer)
            max_duration = request.duration + 10
            try:
                await asyncio.wait_for(
                    self.engine.start_attack(mac, request.type, request.duration),
                    timeout=max_duration,
                )
            except TimeoutError:
                logger.warning(
                    f"Operation on {mac} exceeded maximum duration "
                    f"{max_duration}s, forcing termination"
                )
                await self.engine.stop_attack(mac)
                raise

            # Operation completed successfully
            await self.ws.broadcast(
                {
                    "event": "activeDefenseLog",
                    "data": {
                        "level": "success",
                        "message": f"主动防御完成: {request.type.value} | 目标 {mac}",
                        "mac": mac,
                        "operation_type": request.type.value,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )

            # Update final status
            self.state.update_device_attack_status(mac, ActiveDefenseStatus.IDLE)

            # Log successful completion to audit trail
            await self._log_operation_attempt(
                mac=mac,
                operation_type=request.type.value,
                status="success",
                message=f"Active defense {request.type.value} completed successfully on {mac}",
                user=None,
            )

            logger.info(
                f"Operation {request.type.value} on {mac} completed successfully"
            )

        except asyncio.CancelledError:
            logger.info(f"Operation for {mac} was cancelled by user")
            self.state.update_device_attack_status(mac, ActiveDefenseStatus.STOPPED)
            await self.ws.broadcast(
                {
                    "event": "activeDefenseLog",
                    "data": {
                        "level": "warning",
                        "message": "主动防御操作已取消",
                        "mac": mac,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )
        except Exception as e:
            logger.error(f"Operation execution error for {mac}: {e}", exc_info=True)
            self.state.update_device_attack_status(mac, ActiveDefenseStatus.FAILED)

            # Log failure to audit trail
            await self._log_operation_attempt(
                mac=mac,
                operation_type=request.type.value,
                status="failed",
                message=f"Active defense {request.type.value} failed: {str(e)}",
                user=None,
            )

            await self.ws.broadcast(
                {
                    "event": "activeDefenseLog",
                    "data": {
                        "level": "error",
                        "message": f"主动防御失败: {str(e)}",
                        "mac": mac,
                        "error": str(e),
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )


# Legacy compatibility aliases (will be deprecated in future versions)
AttackService = ActiveDefenseService


# Global service accessor
_service_instance = None


def get_active_defense_service() -> ActiveDefenseService:
    """Get the singleton instance of ActiveDefenseService.

    Returns:
        ActiveDefenseService: The service instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = ActiveDefenseService()
    return _service_instance


# Legacy alias for backward compatibility
def get_attack_service() -> ActiveDefenseService:
    """Legacy alias for get_active_defense_service().

    Deprecated: Use get_active_defense_service() instead.
    This function will be removed in a future version.
    """
    return get_active_defense_service()
