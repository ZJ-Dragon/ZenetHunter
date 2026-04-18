"""Defense executor provider built on top of the legacy engine implementations."""

from __future__ import annotations

import logging

from app.core.engine.base import AttackEngine
from app.core.engine.dummy import DummyAttackEngine
from app.domain.interfaces.providers import CapabilityState, DefenseExecutor

logger = logging.getLogger(__name__)

try:
    from app.core.engine.scapy import ScapyAttackEngine

    _SCAPY_IMPORT_ERROR: str | None = None
except Exception as exc:  # pragma: no cover - depends on local runtime
    ScapyAttackEngine = None  # type: ignore[assignment]
    _SCAPY_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"


class EngineDefenseExecutor(DefenseExecutor):
    """Adapter that exposes legacy engines through the provider contract."""

    name = "engine-defense-executor"

    def __init__(self):
        self._engine, self._capability = self._build_engine()

    @property
    def engine(self) -> AttackEngine:
        return self._engine

    def get_capability(self) -> CapabilityState:
        return self._capability

    async def start(self, target_mac: str, operation_type: str, duration: int) -> None:
        from app.models.attack import ActiveDefenseType

        attack_type = ActiveDefenseType(operation_type)
        await self._engine.start_attack(target_mac, attack_type, duration)

    async def stop(self, target_mac: str) -> None:
        await self._engine.stop_attack(target_mac)

    def _build_engine(self) -> tuple[AttackEngine, CapabilityState]:
        if ScapyAttackEngine is None:
            logger.info("Scapy attack engine import unavailable, using dummy executor")
            return DummyAttackEngine(), CapabilityState(
                name="defense_executor",
                available=False,
                reason=f"Scapy import unavailable: {_SCAPY_IMPORT_ERROR}",
                metadata={
                    "selected_engine": "dummy",
                    "preferred_engine": "scapy",
                    "scapy_import_available": False,
                },
            )

        scapy_engine = ScapyAttackEngine()
        if scapy_engine.check_permissions():
            return scapy_engine, CapabilityState(
                name="defense_executor",
                available=True,
                reason=None,
                metadata={
                    "selected_engine": "scapy",
                    "preferred_engine": "scapy",
                    "scapy_import_available": True,
                },
            )

        logger.warning(
            "Scapy engine imported but is not executable without elevated permissions; "
            "falling back to dummy executor"
        )
        return DummyAttackEngine(), CapabilityState(
            name="defense_executor",
            available=False,
            reason="Scapy is installed but root/CAP_NET_RAW permissions are missing",
            metadata={
                "selected_engine": "dummy",
                "preferred_engine": "scapy",
                "scapy_import_available": True,
            },
        )


_executor_instance: EngineDefenseExecutor | None = None


def get_defense_executor() -> EngineDefenseExecutor:
    """Return the singleton defense executor adapter."""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = EngineDefenseExecutor()
    return _executor_instance
