import asyncio
import logging
from threading import Lock

from app.models.attack import AttackStatus
from app.models.defender import DefenseStatus, DefenseType
from app.models.device import Device, DeviceType
from app.models.log import SystemLog
from app.models.topology import NetworkTopology, TopologyLink, TopologyNode
from app.services.websocket import get_connection_manager

logger = logging.getLogger(__name__)


class StateManager:
    """
    In-memory state manager for devices, logs, and configuration.
    Thread-safe implementation using locks.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._devices: dict[str, Device] = {}
        self._logs: list[SystemLog] = []
        # Simple Allow/Block lists (MAC addresses)
        self._allow_list: set[str] = set()
        self._block_list: set[str] = set()

        self._data_lock = Lock()
        # We need to access WebSocket manager but avoid circular imports if possible.
        # Or use a lazy getter or dependency injection.
        # For singleton pattern, lazy import inside methods is common.
        self._initialized = True

    def _emit_event(self, event_name: str, data: dict) -> None:
        """Emit an event via WebSocket bus (fire and forget)."""
        try:
            # Lazy access to avoid init loops if any
            ws = get_connection_manager()
            # We need to run async broadcast from sync context.
            # If we are in an async loop (FastAPI request), we can use create_task?
            # But StateManager methods might be called from anywhere.
            # Best practice: StateManager should probably be async or we use
            # asyncio.run_coroutine_threadsafe if we have access to the loop.
            # if we have access to the loop.
            # For simplicity in this MVP, we'll assume we are in an async context or
            # we just create a task on the running loop.

            # Check if there is a running loop
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(ws.broadcast({"event": event_name, "data": data}))
            except RuntimeError:
                # No running loop (e.g. synchronous test or script), skip or warn
                logger.warning(
                    f"Could not emit event {event_name}: No running event loop"
                )
        except Exception as e:
            logger.error(f"Failed to emit event {event_name}: {e}")

    def reset(self) -> None:
        """Reset all state (for testing)."""
        with self._data_lock:
            self._devices.clear()
            self._logs.clear()
            self._allow_list.clear()
            self._block_list.clear()

    def get_all_devices(self) -> list[Device]:
        """Return a list of all tracked devices."""
        with self._data_lock:
            return list(self._devices.values())

    def get_device(self, mac: str) -> Device | None:
        """Get a specific device by MAC address."""
        with self._data_lock:
            return self._devices.get(mac.lower())

    def update_device(self, device: Device) -> Device:
        """Update or add a device."""
        with self._data_lock:
            mac = device.mac.lower()
            existing = self._devices.get(mac)

            # Check for status change or new device
            is_new = existing is None
            status_changed = existing and existing.status != device.status

            self._devices[mac] = device

        # Emit events outside lock
        if is_new:
            self._emit_event("deviceAdded", device.model_dump(mode="json"))
        elif status_changed:
            self._emit_event(
                "deviceStatusChanged",
                {
                    "mac": mac,
                    "status": device.status,
                    "device": device.model_dump(mode="json"),
                },
            )

        return device

    def update_device_attack_status(
        self, mac: str, status: AttackStatus
    ) -> Device | None:
        """Update the attack status of a device."""
        with self._data_lock:
            device = self._devices.get(mac.lower())
            if device:
                device.attack_status = status
                self._devices[mac.lower()] = device
                return device
            return None

    def update_device_defense_status(
        self,
        mac: str,
        status: DefenseStatus,
        policy: DefenseType | None = None,
    ) -> Device | None:
        """Update the defense status of a device."""
        with self._data_lock:
            device = self._devices.get(mac.lower())
            if device:
                device.defense_status = status
                if policy is not None:
                    device.active_defense_policy = policy
                elif status == DefenseStatus.INACTIVE:
                    device.active_defense_policy = None

                self._devices[mac.lower()] = device
                return device
            return None

    def get_topology(self) -> NetworkTopology:
        """Generate network topology from device list."""
        with self._data_lock:
            nodes = []
            links = []

            # Assume a simple star topology for now (Gateway <-> Devices)
            # In a real scanner, we might detect the gateway.
            # For now, we'll just list devices as nodes.

            gateway_mac = None

            for mac, device in self._devices.items():
                node_type = "device"
                if device.type == DeviceType.ROUTER:
                    node_type = "router"
                    gateway_mac = mac

                nodes.append(
                    TopologyNode(
                        id=mac,
                        label=device.name or str(device.ip),
                        type=node_type,
                        data=device,
                    )
                )

            # If we have a gateway, link everyone to it
            if gateway_mac:
                for mac in self._devices:
                    if mac != gateway_mac:
                        links.append(
                            TopologyLink(
                                source=gateway_mac,
                                target=mac,
                                type="ethernet",  # Default to ethernet for now
                            )
                        )

            return NetworkTopology(nodes=nodes, links=links)

    def add_log(self, log: SystemLog) -> None:
        """Add a system log entry."""
        with self._data_lock:
            self._logs.append(log)
            # Keep only last 1000 logs to prevent memory leak
            if len(self._logs) > 1000:
                self._logs = self._logs[-1000:]

        # Emit log event
        self._emit_event("logAdded", log.model_dump(mode="json"))

    def get_logs(self, limit: int = 100) -> list[SystemLog]:
        """Get recent system logs."""
        with self._data_lock:
            return sorted(self._logs, key=lambda x: x.timestamp, reverse=True)[:limit]

    # --- List Management ---

    def get_allow_list(self) -> list[str]:
        with self._data_lock:
            return list(self._allow_list)

    def get_block_list(self) -> list[str]:
        with self._data_lock:
            return list(self._block_list)

    def add_to_allow_list(self, mac: str) -> None:
        with self._data_lock:
            self._allow_list.add(mac.lower())
            # Remove from block list if present
            if mac.lower() in self._block_list:
                self._block_list.remove(mac.lower())

    def add_to_block_list(self, mac: str) -> None:
        with self._data_lock:
            self._block_list.add(mac.lower())
            # Remove from allow list if present
            if mac.lower() in self._allow_list:
                self._allow_list.remove(mac.lower())

    def remove_from_lists(self, mac: str) -> None:
        with self._data_lock:
            if mac.lower() in self._allow_list:
                self._allow_list.remove(mac.lower())
            if mac.lower() in self._block_list:
                self._block_list.remove(mac.lower())


# Global accessor
def get_state_manager() -> StateManager:
    return StateManager()
