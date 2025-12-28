import logging

from fastapi import HTTPException

from app.core.engine.arp_monitor import ArpMonitor
from app.core.engine.defense_factory import get_defense_engine
from app.core.engine.dns_rpz import DnsRpzEngine, DummyDnsRpzEngine
from app.core.engine.dummy_ap import DummyAccessPointManager
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
    DefensePolicy(
        id=DefenseType.UDP_RATE_LIMIT,
        name="UDP Traffic Rate Limiting (Global)",
        description=(
            "Apply traffic control (tc) to limit UDP packet rates "
            "and prevent flood attacks."
        ),
    ),
    DefensePolicy(
        id=DefenseType.ARP_DAI,
        name="ARP Inspection & Monitoring",
        description=(
            "Detect ARP spoofing via passive monitoring "
            "or manage Switch DAI capabilities."
        ),
    ),
    DefensePolicy(
        id=DefenseType.DNS_RPZ,
        name="DNS Sinkhole / RPZ",
        description=(
            "Block or redirect malicious domains using DNS Response Policy Zones."
        ),
    ),
    DefensePolicy(
        id=DefenseType.TCP_RESET_POLICY,
        name="TCP Reset Policy (Active Defense)",
        description=(
            "Quickly terminate unauthorized connections using TCP RST "
            "and ICMP rejections to prevent resource exhaustion."
        ),
    ),
    DefensePolicy(
        id=DefenseType.WALLED_GARDEN,
        name="Walled Garden / Captive Portal",
        description=(
            "Restrict unauthorized devices to Portal page and whitelisted services. "
            "All other traffic is redirected or blocked."
        ),
    ),
    DefensePolicy(
        id=DefenseType.WPA3_8021X,
        name="WPA3/802.1X Enterprise Access Control",
        description=(
            "Configure WPA3-Personal/Enterprise with 802.1X authentication. "
            "Supports RADIUS integration and VLAN-based policy assignment."
        ),
    ),
    DefensePolicy(
        id=DefenseType.TARPIT,
        name="TCP Tarpit (Optional)",
        description=(
            "Slow down unauthorized connections by keeping them open but "
            "responding extremely slowly. Reduces scanning efficiency. "
            "Requires xtables-addons or nf_tarpit kernel module."
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
        # Initialize ARP Monitor (singleton-ish within service)
        self.arp_monitor = ArpMonitor()
        # Initialize DNS RPZ Engine (currently dummy, future factory)
        self.dns_engine: DnsRpzEngine = DummyDnsRpzEngine()
        # Initialize Access Point Manager (currently dummy, future factory)
        self.ap_manager = DummyAccessPointManager()

    def get_policies(self) -> list[DefensePolicy]:
        """Return list of available defense policies."""
        return AVAILABLE_POLICIES

    async def apply_defense(self, mac: str, request: DefenseApplyRequest) -> None:
        """
        Apply a defense policy to a device.
        """
        # Special handling for global policies
        if request.policy in [
            DefenseType.SYN_PROXY,
            DefenseType.UDP_RATE_LIMIT,
            DefenseType.ARP_DAI,
            DefenseType.DNS_RPZ,
            DefenseType.TCP_RESET_POLICY,
            DefenseType.WALLED_GARDEN,
            DefenseType.WPA3_8021X,
            DefenseType.TARPIT,
        ]:
            if mac.lower() != "global":
                # Global policies are usually interface-based, not MAC-based
                logger.warning(
                    f"{request.policy} is a global policy, but applied to specific MAC."
                )

            if request.policy == DefenseType.ARP_DAI:
                await self.arp_monitor.start_monitoring()
                # Also trigger switch DAI if implemented in engine
                await self.engine.enable_global_protection(request.policy)
            elif request.policy == DefenseType.DNS_RPZ:
                # For MVP, enable a default blocklist
                await self.dns_engine.add_zone("blacklist")
                await self.dns_engine.add_rule("malware.test", "NXDOMAIN")
            elif request.policy == DefenseType.WPA3_8021X:
                # WPA3/802.1X is typically a global wireless network configuration
                # For MVP, we log that it would be configured
                # In production, this would call AP manager to configure SSID/RADIUS
                logger.info(
                    "[DefenderService] WPA3/802.1X configuration requested. "
                    "This requires AP manager integration."
                )
            else:
                await self.engine.enable_global_protection(request.policy)
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
        # For now, assume if mac is 'global', we try to stop all global policies
        # Ideally stop_defense should take a policy argument too.
        if mac == "global":
            # Stop known global policies
            await self.engine.disable_global_protection(DefenseType.SYN_PROXY)
            await self.engine.disable_global_protection(DefenseType.UDP_RATE_LIMIT)
            await self.engine.disable_global_protection(DefenseType.TCP_RESET_POLICY)
            await self.engine.disable_global_protection(DefenseType.WALLED_GARDEN)
            await self.engine.disable_global_protection(DefenseType.TARPIT)
            # Stop ARP Monitor
            await self.arp_monitor.stop_monitoring()
            await self.engine.disable_global_protection(DefenseType.ARP_DAI)
            # WPA3/802.1X is persistent configuration, no explicit "stop"
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
