"""Abstract base class for defense engines."""

from abc import ABC, abstractmethod
from typing import Any

from app.models.defender import DefenseType


class DefenseEngine(ABC):
    """Interface for defense engines (e.g. Iptables, NFTables, Dummy)."""

    @abstractmethod
    def check_capabilities(self) -> bool:
        """Check if the engine has sufficient permissions and system capabilities."""
        pass

    @abstractmethod
    async def apply_policy(
        self, target: str, policy: DefenseType, params: dict[str, Any] | None = None
    ) -> None:
        """
        Apply a defense policy to a target.
        
        Args:
            target: Target identifier (MAC or IP depending on context)
            policy: The policy type to apply
            params: Optional parameters for the policy
        """
        pass

    @abstractmethod
    async def remove_policy(self, target: str, policy: DefenseType) -> None:
        """Remove a defense policy from a target."""
        pass

    @abstractmethod
    async def enable_global_protection(self, policy: DefenseType) -> None:
        """Enable a global protection mechanism (e.g. SYNPROXY for the gateway)."""
        pass

    @abstractmethod
    async def disable_global_protection(self, policy: DefenseType) -> None:
        """Disable a global protection mechanism."""
        pass

