"""Runtime environment and dependency diagnostics."""

from __future__ import annotations

import importlib
import os
import platform
import sys
from dataclasses import asdict, dataclass, field


REQUIRED_MODULES: dict[str, str] = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "sqlalchemy": "sqlalchemy",
    "aiosqlite": "aiosqlite",
    "asyncpg": "asyncpg",
    "pyjwt": "jwt",
    "python_multipart": "multipart",
    "pyyaml": "yaml",
    "httpx": "httpx",
    "pydantic_settings": "pydantic_settings",
    "scapy": "scapy.all",
}


@dataclass(slots=True)
class ModuleCheck:
    """Single import check result."""

    name: str
    import_name: str
    available: bool
    error: str | None = None


@dataclass(slots=True)
class RuntimeDiagnostics:
    """Collected runtime diagnostics for startup and support screens."""

    python_executable: str
    python_version: str
    platform: str
    is_root: bool
    environment_kind: str
    environment_name: str | None
    virtual_env: str | None
    conda_env: str | None
    modules: dict[str, ModuleCheck] = field(default_factory=dict)

    @property
    def missing_modules(self) -> list[str]:
        return [
            name
            for name, module in self.modules.items()
            if not module.available
        ]

    @property
    def dependencies_ready(self) -> bool:
        return not self.missing_modules

    def to_dict(self) -> dict[str, object]:
        """Convert diagnostics into a JSON-serializable dictionary."""
        return {
            "python_executable": self.python_executable,
            "python_version": self.python_version,
            "platform": self.platform,
            "is_root": self.is_root,
            "environment_kind": self.environment_kind,
            "environment_name": self.environment_name,
            "virtual_env": self.virtual_env,
            "conda_env": self.conda_env,
            "dependencies_ready": self.dependencies_ready,
            "missing_modules": self.missing_modules,
            "modules": {
                name: asdict(module) for name, module in self.modules.items()
            },
        }


def collect_runtime_diagnostics() -> RuntimeDiagnostics:
    """Inspect the current interpreter, environment, and required modules."""
    diagnostics = RuntimeDiagnostics(
        python_executable=sys.executable,
        python_version=platform.python_version(),
        platform=sys.platform,
        is_root=_is_root(),
        environment_kind=_detect_environment_kind(),
        environment_name=_detect_environment_name(),
        virtual_env=os.getenv("VIRTUAL_ENV"),
        conda_env=os.getenv("CONDA_DEFAULT_ENV"),
    )
    diagnostics.modules = {
        name: _check_module(name, import_name)
        for name, import_name in REQUIRED_MODULES.items()
    }
    return diagnostics


def _check_module(name: str, import_name: str) -> ModuleCheck:
    try:
        importlib.import_module(import_name)
        return ModuleCheck(
            name=name,
            import_name=import_name,
            available=True,
        )
    except Exception as exc:  # pragma: no cover - runtime-dependent
        return ModuleCheck(
            name=name,
            import_name=import_name,
            available=False,
            error=f"{type(exc).__name__}: {exc}",
        )


def _is_root() -> bool:
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


def _detect_environment_kind() -> str:
    conda_env = os.getenv("CONDA_DEFAULT_ENV")
    if conda_env and conda_env != "base":
        return "conda"
    if os.getenv("VIRTUAL_ENV"):
        return "venv"
    return "system"


def _detect_environment_name() -> str | None:
    conda_env = os.getenv("CONDA_DEFAULT_ENV")
    if conda_env and conda_env != "base":
        return conda_env

    virtual_env = os.getenv("VIRTUAL_ENV")
    if virtual_env:
        return os.path.basename(virtual_env.rstrip(os.sep))

    return None
