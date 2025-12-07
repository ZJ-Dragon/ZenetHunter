"""Q-Table Persistence Service for AI Scheduler."""

import hashlib
import json
import logging
from pathlib import Path
from threading import Lock
from typing import Any

from app.models.scheduler import QEntry, QTable, StrategyIdentifier

logger = logging.getLogger(__name__)


class QTablePersistence:
    """
    Service for persisting and loading Q-tables.
    Supports file-based persistence (JSON) for MVP.
    """

    def __init__(self, storage_path: Path | str | None = None):
        """
        Initialize Q-table persistence.

        Args:
            storage_path: Path to storage directory. Defaults to ./data/qtable.json
        """
        if storage_path is None:
            storage_path = Path("./data/qtable.json")
        elif isinstance(storage_path, str):
            storage_path = Path(storage_path)

        self.storage_path = storage_path
        self._lock = Lock()
        self._qtable: QTable | None = None

    def load(self) -> QTable:
        """Load Q-table from storage."""
        with self._lock:
            if self._qtable is not None:
                return self._qtable

            if not self.storage_path.exists():
                logger.info(
                    f"Q-table file not found at {self.storage_path}, creating new table"
                )
                self._qtable = QTable()
                return self._qtable

            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)

                # Reconstruct Q-table from JSON
                entries = {}
                for key, entry_data in data.get("entries", {}).items():
                    # Reconstruct StrategyIdentifier
                    strategy_data = entry_data["strategy"]
                    strategy = StrategyIdentifier(
                        type=strategy_data["type"], strategy_id=strategy_data["strategy_id"]
                    )
                    entries[key] = QEntry(
                        device_state_hash=entry_data["device_state_hash"],
                        strategy=strategy,
                        q_value=entry_data["q_value"],
                        visit_count=entry_data["visit_count"],
                        last_updated=entry_data["last_updated"],
                    )

                self._qtable = QTable(
                    entries=entries,
                    learning_rate=data.get("learning_rate", 0.1),
                    discount_factor=data.get("discount_factor", 0.9),
                    last_updated=data.get("last_updated"),
                )

                logger.info(f"Loaded Q-table with {len(entries)} entries")
                return self._qtable

            except Exception as e:
                logger.error(f"Failed to load Q-table: {e}, creating new table")
                self._qtable = QTable()
                return self._qtable

    def save(self, qtable: QTable | None = None) -> None:
        """Save Q-table to storage."""
        with self._lock:
            if qtable is not None:
                self._qtable = qtable

            if self._qtable is None:
                logger.warning("No Q-table to save")
                return

            # Ensure directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                # Convert Q-table to JSON-serializable format
                data = {
                    "entries": {},
                    "learning_rate": self._qtable.learning_rate,
                    "discount_factor": self._qtable.discount_factor,
                    "last_updated": self._qtable.last_updated.isoformat(),
                }

                for key, entry in self._qtable.entries.items():
                    data["entries"][key] = {
                        "device_state_hash": entry.device_state_hash,
                        "strategy": {
                            "type": entry.strategy.type.value,
                            "strategy_id": entry.strategy.strategy_id.value,
                        },
                        "q_value": entry.q_value,
                        "visit_count": entry.visit_count,
                        "last_updated": entry.last_updated.isoformat(),
                    }

                with open(self.storage_path, "w") as f:
                    json.dump(data, f, indent=2)

                logger.info(f"Saved Q-table with {len(self._qtable.entries)} entries")

            except Exception as e:
                logger.error(f"Failed to save Q-table: {e}")

    def get_qtable(self) -> QTable:
        """Get current Q-table (loads if not already loaded)."""
        if self._qtable is None:
            return self.load()
        return self._qtable

    def compute_device_state_hash(self, device_data: dict[str, Any]) -> str:
        """
        Compute a hash for device state.
        Used to create consistent state representations for Q-learning.

        Args:
            device_data: Dictionary containing device features (MAC, type, ports, etc.)

        Returns:
            SHA256 hash of device state
        """
        # Create a deterministic representation of device state
        state_str = json.dumps(device_data, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()[:16]  # Use first 16 chars

