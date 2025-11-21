import logging

from fastapi import HTTPException

from app.models.defender import (
    DefenseApplyRequest,
    DefensePolicy,
    DefenseStatus,
    DefenseType,
)
from app.services.state import get_state_manager
from app.services.websocket import get_connection_manager

logger = logging.getLogger(__name__)

AVAILABLE_POLICIES = [
    DefensePolicy(
        id=DefenseType.QUARANTINE,
        name="Quarantine Device",
        description="Completely isolate the device from the network (Walled Garden).",
    ),
    DefensePolicy(
        id=DefenseType.BLOCK_WAN,
        name="Block Internet Access",
        description="Prevent the device from accessing the WAN/Internet.",
    ),
]


class DefenderService:
    """
    Service for managing defense mechanisms on devices.
    Orchestrates the application of policies and state updates.
    """

    def __init__(self):
        self.state_manager = get_state_manager()
        self.ws_manager = get_connection_manager()

    def get_policies(self) -> list[DefensePolicy]:
        """Return list of available defense policies."""
        return AVAILABLE_POLICIES

    async def apply_defense(self, mac: str, request: DefenseApplyRequest) -> None:
        """
        Apply a defense policy to a device.

        Args:
            mac: MAC address of target device
            request: Defense configuration

        Raises:
            HTTPException: If device not found
        """
        device = self.state_manager.get_device(mac)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        current_status = device.defense_status

        # Determine event type
        event_name = (
            "defenseStarted"
            if current_status == DefenseStatus.INACTIVE
            else "defenseUpdated"
        )

        # Update state
        updated_device = self.state_manager.update_device_defense_status(
            mac, DefenseStatus.ACTIVE, request.policy
        )

        if updated_device:
            logger.info(
                f"Applying defense policy '{request.policy}' to {mac}. "
                f"Event: {event_name}"
            )

            # Broadcast event
            await self.ws_manager.broadcast(
                {
                    "event": event_name,
                    "data": {
                        "mac": mac,
                        "policy": request.policy,
                        "status": DefenseStatus.ACTIVE,
                    },
                }
            )

            # TODO: Integrate with AttackEngine/PacketManipulator to actually
            # enforce the policy (e.g. ARP Spoofing, IPTables).
            # For now, this is a control plane implementation.

    async def stop_defense(self, mac: str) -> None:
        """
        Stop any active defense on a device.

        Args:
            mac: MAC address of target device

        Raises:
            HTTPException: If device not found
        """
        device = self.state_manager.get_device(mac)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        if device.defense_status == DefenseStatus.INACTIVE:
            return  # Already stopped

        # Update state
        self.state_manager.update_device_defense_status(mac, DefenseStatus.INACTIVE)

        logger.info(f"Stopping defense on {mac}")

        # Broadcast event
        await self.ws_manager.broadcast(
            {
                "event": "defenseStopped",
                "data": {
                    "mac": mac,
                    "status": DefenseStatus.INACTIVE,
                },
            }
        )
