import logging
from threading import Lock

from app.models.attack import AttackStatus
from app.models.device import Device, DeviceType
from app.models.log import SystemLog
from app.models.topology import NetworkTopology, TopologyLink, TopologyNode

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
        self._initialized = True

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
            self._devices[device.mac.lower()] = device
            return device

    def update_device_attack_status(
        self, mac: str, status: AttackStatus
    ) -> Device | None:
        """Update the attack status of a device."""
        with self._data_lock:
            device = self._devices.get(mac.lower())
            if device:
                device.attack_status = status
                # Pydantic v2 models are mutable by default if not frozen
                # But to be safe and trigger updates if we had observers, we re-set it
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
