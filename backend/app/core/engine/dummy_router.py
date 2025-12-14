import asyncio
import hashlib

from app.core.engine.base_router import RouterManager
from app.models.router_integration import ACLRule, IsolationPolicy, RateLimitPolicy


class DummyRouterManager(RouterManager):
    """In-memory dummy adapter for development and testing.

    Simulates router features without touching real devices.
    """

    def __init__(self) -> None:
        # State stores
        self._rate_limits: dict[str, RateLimitPolicy] = {}
        self._isolation: dict[str, IsolationPolicy] = {}
        self._acl_rules: dict[str, ACLRule] = {}

        # Timers for auto-revert (per target)
        self._timers: dict[str, asyncio.Task] = {}

    # ---- helpers -----------------------------------------------------------
    def _fingerprint_rule(self, rule: ACLRule) -> str:
        key = "|".join(
            [
                rule.src.lower(),
                rule.dst.lower(),
                rule.proto.value,
                (rule.port or "*"),
                rule.action.value,
                str(rule.priority),
            ]
        )
        return hashlib.sha1(key.encode("utf-8")).hexdigest()

    def _schedule_revert(self, key: str, seconds: int, coro_factory):
        # Cancel existing timer for the key
        task = self._timers.get(key)
        if task and not task.done():
            task.cancel()

        async def _job():
            try:
                await asyncio.sleep(seconds)
                await coro_factory()
            except asyncio.CancelledError:
                pass

        self._timers[key] = asyncio.create_task(_job())

    # ---- RouterManager implementation -------------------------------------
    async def set_rate_limit(self, policy: RateLimitPolicy) -> bool:
        self._rate_limits[policy.target_mac] = policy
        if policy.duration:
            self._schedule_revert(
                f"rl:{policy.target_mac}",
                policy.duration,
                lambda: self.remove_rate_limit(policy.target_mac),
            )
        return True

    async def remove_rate_limit(self, target_mac: str) -> bool:
        existed = target_mac in self._rate_limits
        self._rate_limits.pop(target_mac, None)
        # Cancel timer if any
        t = self._timers.pop(f"rl:{target_mac}", None)
        if t and not t.done():
            t.cancel()
        return existed or True  # treat no-op as success

    async def apply_acl_rule(self, rule: ACLRule) -> str:
        rule_id = rule.rule_id or self._fingerprint_rule(rule)
        # Idempotent apply
        self._acl_rules[rule_id] = ACLRule(**{**rule.model_dump(), "rule_id": rule_id})
        return rule_id

    async def remove_acl_rule(self, rule_id: str) -> bool:
        existed = rule_id in self._acl_rules
        self._acl_rules.pop(rule_id, None)
        return existed or True

    async def isolate_device(self, policy: IsolationPolicy) -> bool:
        self._isolation[policy.target_mac] = policy
        if policy.duration:
            self._schedule_revert(
                f"iso:{policy.target_mac}",
                policy.duration,
                lambda: self.reintegrate_device(policy.target_mac),
            )
        return True

    async def reintegrate_device(self, target_mac: str) -> bool:
        existed = target_mac in self._isolation
        self._isolation.pop(target_mac, None)
        t = self._timers.pop(f"iso:{target_mac}", None)
        if t and not t.done():
            t.cancel()
        return existed or True
