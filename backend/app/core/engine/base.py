"""Abstract base class for attack engines."""

from abc import ABC, abstractmethod

from app.models.attack import AttackType


class AttackEngine(ABC):
    """Interface for attack engines (e.g. Dummy, Scapy, Nmap)."""

    @abstractmethod
    def check_permissions(self) -> bool:
        """Check if the engine has sufficient permissions (e.g. root)."""
        pass

    @abstractmethod
    async def start_attack(
        self, target_mac: str, attack_type: AttackType, duration: int
    ) -> None:
        """Start an attack on a specific target."""
        pass

    @abstractmethod
    async def stop_attack(self, target_mac: str) -> None:
        """Stop an attack on a specific target."""
        pass
