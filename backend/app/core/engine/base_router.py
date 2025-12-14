"""Router management abstraction (rate limit, ACL, guest isolation).

This base class defines the contract that vendor-specific adapters must follow.
"""

from abc import ABC, abstractmethod

from app.models.router_integration import ACLRule, IsolationPolicy, RateLimitPolicy


class RouterManager(ABC):
    """Interface for managing router features used by ZenetHunter.

    Adapters implement device/vendor-specific logic (e.g., REST, SSH, NETCONF).
    """

    # ---- Rate limiting -----------------------------------------------------
    @abstractmethod
    async def set_rate_limit(self, policy: RateLimitPolicy) -> bool:
        """Apply per-device rate limit. Returns True if updated/applied."""
        raise NotImplementedError

    @abstractmethod
    async def remove_rate_limit(self, target_mac: str) -> bool:
        """Remove per-device rate limit. Returns True if removed/no-op."""
        raise NotImplementedError

    # ---- ACL ---------------------------------------------------------------
    @abstractmethod
    async def apply_acl_rule(self, rule: ACLRule) -> str:
        """Apply ACL rule and return stable rule_id.

        Adapters should implement idempotency using a rule fingerprint
        so that re-applying an equivalent rule returns the same rule_id.
        """
        raise NotImplementedError

    @abstractmethod
    async def remove_acl_rule(self, rule_id: str) -> bool:
        """Remove ACL rule by rule_id. Returns True if removed/no-op."""
        raise NotImplementedError

    # ---- Guest isolation ---------------------------------------------------
    @abstractmethod
    async def isolate_device(self, policy: IsolationPolicy) -> bool:
        """Isolate a device according to policy. Returns True on success."""
        raise NotImplementedError

    @abstractmethod
    async def reintegrate_device(self, target_mac: str) -> bool:
        """Revert isolation for the device. Returns True if changed/no-op."""
        raise NotImplementedError
