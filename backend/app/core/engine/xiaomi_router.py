"""Xiaomi Router QoS adapter (mock-first).

This adapter implements RouterManager for Xiaomi MiWiFi series.
Default behavior is MOCK (no network I/O) unless connection params are
provided via settings (router_host and credentials). Live HTTP paths are
structured but only executed when explicitly configured to avoid adding
hard runtime deps.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings
from app.core.engine.base_router import RouterManager
from app.models.router_integration import ACLRule, IsolationPolicy, RateLimitPolicy

logger = logging.getLogger(__name__)


@dataclass
class _Conn:
    host: str | None
    username: str | None
    password: str | None
    token: str | None  # some firmwares use stok token after login


class XiaomiRouterManager(RouterManager):
    """RouterManager implementation for Xiaomi MiWiFi (QoS/limits).

    Capabilities in this placeholder implementation:
    - Rate limit: supported (mock; live path when configured)
    - ACL: no native generic ACL on consumer models → treated as no-op success
    - Isolation: no direct mapping → treated as no-op success
    """

    def __init__(self) -> None:
        s = get_settings()
        # Reuse generic router_* settings; token is optional (can be set in password)
        token = None
        # Allow passing token inside password as "stok:<value>" for quick tests
        if getattr(s, "router_password", None) and str(s.router_password).startswith(
            "stok:"
        ):
            token = str(s.router_password)[5:]
        self.conn = _Conn(
            host=getattr(s, "router_host", None),
            username=getattr(s, "router_username", None),
            password=getattr(s, "router_password", None),
            token=token,
        )

        # In-memory state for MOCK mode
        self._rate_limits: dict[str, RateLimitPolicy] = {}
        self._acl_rules: dict[str, ACLRule] = {}
        self._isolation: dict[str, IsolationPolicy] = {}
        self._timers: dict[str, asyncio.Task] = {}

    # ---- helpers -----------------------------------------------------------
    def _mock(self) -> bool:
        # Mock when no host provided
        return not self.conn.host

    def _fp_rule(self, rule: ACLRule) -> str:
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

    def _schedule(self, key: str, seconds: int, coro_factory) -> None:
        t = self._timers.get(key)
        if t and not t.done():
            t.cancel()

        async def _job():
            try:
                await asyncio.sleep(seconds)
                await coro_factory()
            except asyncio.CancelledError:
                pass

        self._timers[key] = asyncio.create_task(_job())

    # ---- RouterManager implementation -------------------------------------
    async def set_rate_limit(self, policy: RateLimitPolicy) -> bool:
        if self._mock():
            self._rate_limits[policy.target_mac] = policy
            if policy.duration:
                self._schedule(
                    f"rl:{policy.target_mac}",
                    policy.duration,
                    lambda: self.remove_rate_limit(policy.target_mac),
                )
            return True

        # Live path (best-effort; only when configured). Import lazily.
        try:
            import httpx  # type: ignore

            async with httpx.AsyncClient(base_url=self._base_url()) as client:
                # Xiaomi MiWiFi QoS endpoints differ by firmware.
                # Typical pattern: /cgi-bin/luci/;stok=<stok>/api/xqos/ ...
                # Here we simulate per-device limit via setdevice or set_speedlimit.
                payload: dict[str, Any] = {
                    "mac": policy.target_mac,
                    # Convert kbps to MiWiFi expected units when necessary (kbps ok)
                    "upload": policy.up_kbps if policy.up_kbps is not None else 0,
                    "download": policy.down_kbps if policy.down_kbps is not None else 0,
                }
                r = await client.post("/api/xqos/setdevice", data=payload)
                r.raise_for_status()
                js = r.json()
                ok = js.get("code") in (0, "0", "OK") or js.get("errcode") == 0
                if ok and policy.duration:
                    self._schedule(
                        f"rl:{policy.target_mac}",
                        policy.duration,
                        lambda: self.remove_rate_limit(policy.target_mac),
                    )
                return bool(ok)
        except Exception as e:  # pragma: no cover - network errors
            logger.warning("Xiaomi QoS live call failed, falling back to mock: %s", e)
            # Fall back to mock to keep API usable
            self._rate_limits[policy.target_mac] = policy
            return True

    async def remove_rate_limit(self, target_mac: str) -> bool:
        if self._mock():
            existed = target_mac in self._rate_limits
            self._rate_limits.pop(target_mac, None)
            t = self._timers.pop(f"rl:{target_mac}", None)
            if t and not t.done():
                t.cancel()
            return existed or True

        try:
            import httpx  # type: ignore

            async with httpx.AsyncClient(base_url=self._base_url()) as client:
                r = await client.post(
                    "/api/xqos/cleardevice",
                    data={"mac": target_mac},
                )
                r.raise_for_status()
                js = r.json()
                ok = js.get("code") in (0, "0", "OK") or js.get("errcode") == 0
                return bool(ok)
        except Exception as e:  # pragma: no cover
            logger.warning("Xiaomi QoS remove live call failed: %s", e)
            return True  # treat as success to avoid blocking flows

    async def apply_acl_rule(self, rule: ACLRule) -> str:
        # No general ACL on consumer MiWiFi → no-op with stable id
        rule_id = rule.rule_id or self._fp_rule(rule)
        self._acl_rules[rule_id] = ACLRule(**{**rule.model_dump(), "rule_id": rule_id})
        return rule_id

    async def remove_acl_rule(self, rule_id: str) -> bool:
        existed = rule_id in self._acl_rules
        self._acl_rules.pop(rule_id, None)
        return existed or True

    async def isolate_device(self, policy: IsolationPolicy) -> bool:
        # No direct isolation control via MiWiFi public API → track state only
        self._isolation[policy.target_mac] = policy
        if policy.duration:
            self._schedule(
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

    # ---- internal ----------------------------------------------------------
    def _base_url(self) -> str:
        # Build base url with stok prefix when provided
        host = self.conn.host or "http://miwifi.com"
        host = host.rstrip("/")
        if self.conn.token:
            return f"{host}/cgi-bin/luci/;stok={self.conn.token}"
        return f"{host}/cgi-bin/luci"
