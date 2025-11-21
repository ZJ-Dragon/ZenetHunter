import logging

from fastapi import HTTPException

from app.core.engine.defense_factory import get_defense_engine
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
    DefensePolicy(
        id=DefenseType.SYN_PROXY,
        name="SYN Flood Protection (Global)",
        description=(
            "Enable kernel-level SYN Proxy on gateway interface to mitigate SYN floods."
        ),
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
        self.engine = get_defense_engine()

    def get_policies(self) -> list[DefensePolicy]:
        """Return list of available defense policies."""
        return AVAILABLE_POLICIES

    async def apply_defense(self, mac: str, request: DefenseApplyRequest) -> None:
        """
        Apply a defense policy to a device.
        """
        # Special handling for global policies
        if request.policy == DefenseType.SYN_PROXY:
            if mac.lower() != "global":
                # We could allow specific IPs, but SYNPROXY is usually interface-based
                logger.warning(
                    "SYN_PROXY is a global policy, but applied to specific MAC."
                )

            await self.engine.enable_global_protection(request.policy)
            # Global state tracking is not yet in Device model,
            # but we can treat '00:00:00:00:00:00' or similar as a system object later.
            # For now, we just execute the engine command.
            return

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

        # Apply via Engine
        await self.engine.apply_policy(mac, request.policy)

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
        """
        # Special handling for global policies - simplistic for now
        # We need to know WHAT policy to stop.
        # For now, assume if mac is 'global', we stop SYN_PROXY
        if mac == "global":
            await self.engine.disable_global_protection(DefenseType.SYN_PROXY)
            return

        device = self.state_manager.get_device(mac)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        if device.defense_status == DefenseStatus.INACTIVE:
            return  # Already stopped

        active_policy = device.active_defense_policy

        # Call engine to remove rules
        if active_policy:
            await self.engine.remove_policy(mac, active_policy)

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
