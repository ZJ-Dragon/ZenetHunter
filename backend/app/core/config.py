"""Application settings (12‑Factor style).

Primary source of truth for runtime configuration. Values are loaded from
**environment variables** and exposed as a typed settings object. We use
`pydantic-settings` when available (FastAPI‑recommended), with a safe fallback
that reads directly from `os.environ`.

References:
- 12‑Factor "Config": store config in the environment. https://12factor.net/config
- FastAPI docs: Settings via Pydantic Settings and optional `.env`. https://fastapi.tiangolo.com/advanced/settings/
- Pydantic Settings (v2): https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- Python logging levels semantics: https://docs.python.org/3/howto/logging.html
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any, Literal

try:
    # Preferred path: pydantic-settings (v2)
    from pydantic import BaseModel, Field, field_validator, model_validator
    from pydantic_settings import BaseSettings, SettingsConfigDict

    _HAVE_PYDANTIC_SETTINGS = True
except Exception:  # pragma: no cover
    # Fallback path: use BaseModel + manual env fetch
    from pydantic import BaseModel, Field

    _HAVE_PYDANTIC_SETTINGS = False


# ---- helpers ---------------------------------------------------------------
_DEFAULT_CORS = "http://localhost:5173"
_ALLOWED_LOG_LEVELS = {"debug", "info", "warning", "error", "critical"}


def _split_csv(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [v.strip() for v in value if v and v.strip()]
    # comma-separated string
    return [v.strip() for v in value.split(",") if v and v.strip()]


# ---- settings model (preferred: pydantic-settings) -------------------------
if _HAVE_PYDANTIC_SETTINGS:

    class Settings(BaseSettings):
        """Typed application settings (env‑driven).

        Environment variable mapping uses explicit aliases so names remain
        stable, e.g. `APP_ENV`, `APP_HOST`, `APP_PORT`, `LOG_LEVEL`,
        `DATABASE_URL`, `CORS_ORIGINS`.
        """

        # Meta
        app_name: str = Field(
            default="ZenetHunter API",
            # Also accepts APP_NAME for backward compatibility
            validation_alias="API_TITLE",
        )
        app_version: str = Field(
            default_factory=lambda: os.getenv("API_VERSION")
            or os.getenv("APP_VERSION", "0.1.0")
        )

        # Runtime
        app_env: Literal["development", "staging", "production"] = Field(
            default="development",
            validation_alias="APP_ENV",
        )
        app_host: str = Field(default="0.0.0.0", validation_alias="APP_HOST")
        app_port: int = Field(default=8000, validation_alias="APP_PORT")

        # Logging - environment-specific defaults
        log_level: str = Field(default="info", validation_alias="LOG_LEVEL")

        # Security
        secret_key: str = Field(
            default="insecure-dev-secret-key-do-not-use-in-production",
            validation_alias="SECRET_KEY",
        )
        
        # Active Defense Kill-Switch (Safety Control)
        active_defense_enabled: bool = Field(
            default=False,
            validation_alias="ACTIVE_DEFENSE_ENABLED",
            description="Global kill-switch for active defense operations. Must be explicitly enabled."
        )
        active_defense_readonly: bool = Field(
            default=False,
            validation_alias="ACTIVE_DEFENSE_READONLY",
            description="Read-only mode: allows querying but prevents execution of operations"
        )

        # External services (optional in early project phases)
        database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")

        # Integration: Router adapter selection & connection params
        router_adapter: str = Field(default="dummy", validation_alias="ROUTER_ADAPTER")
        router_host: str | None = Field(default=None, validation_alias="ROUTER_HOST")
        router_port: int | None = Field(default=None, validation_alias="ROUTER_PORT")
        router_username: str | None = Field(
            default=None, validation_alias="ROUTER_USERNAME"
        )
        router_password: str | None = Field(
            default=None, validation_alias="ROUTER_PASSWORD"
        )

        # Integration: Webhook verification
        webhook_secret: str = Field(
            default="dev-webhook-secret", validation_alias="WEBHOOK_SECRET"
        )
        webhook_tolerance_sec: int = Field(
            default=300, validation_alias="WEBHOOK_TOLERANCE_SEC"
        )

        # Active Scanning Configuration
        scan_range: str = Field(
            default="192.168.1.0/24",
            validation_alias="SCAN_RANGE",
            description="CIDR range for network scanning",
        )
        scan_timeout_sec: int = Field(
            default=30, validation_alias="SCAN_TIMEOUT_SEC", description="Scan timeout"
        )
        scan_concurrency: int = Field(
            default=10,
            validation_alias="SCAN_CONCURRENCY",
            description="Max concurrent probes",
        )
        scan_interval_sec: int | None = Field(
            default=None,
            validation_alias="SCAN_INTERVAL_SEC",
            description="Interval for periodic scans (None = manual only)",
        )

        # Feature Flags for Enrichment
        feature_mdns: bool = Field(
            default=True, validation_alias="FEATURE_MDNS", description="Enable mDNS"
        )
        feature_ssdp: bool = Field(
            default=True, validation_alias="FEATURE_SSDP", description="Enable SSDP"
        )
        feature_nbns: bool = Field(
            default=False,
            validation_alias="FEATURE_NBNS",
            description="Enable NBNS (Windows)",
        )
        feature_snmp: bool = Field(
            default=False,
            validation_alias="FEATURE_SNMP",
            description="Enable SNMP (requires credentials)",
        )
        feature_fingerbank: bool = Field(
            default=False,
            validation_alias="FEATURE_FINGERBANK",
            description="Enable Fingerbank API (external, default off)",
        )

        # CORS: comma‑separated list → list[str]
        cors_origins_raw: str = Field(
            default_factory=lambda: os.getenv("CORS_ALLOW_ORIGINS")
            or os.getenv("CORS_ORIGINS", _DEFAULT_CORS)
        )
        cors_origins: list[str] = Field(default_factory=list)

        # Model & source configuration
        model_config = SettingsConfigDict(
            # Support .env files for local development (requires python-dotenv)
            # pydantic-settings will automatically look for .env files in:
            # 1. Current working directory
            # 2. Parent directories (up to the filesystem root)
            # Set env_file=".env" explicitly if you want to restrict to a specific path
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )

        @model_validator(mode="after")
        def _apply_env_defaults(self) -> Settings:
            """Apply environment-specific default values after model validation."""
            env = self.app_env.lower()
            # Set log level defaults based on environment (only if not explicitly set)
            if not os.getenv("LOG_LEVEL"):
                if env == "development" and self.log_level == "info":
                    # Only override if still at default "info"
                    self.log_level = "debug"
                elif env == "staging" and self.log_level == "info":
                    # Keep info for staging
                    pass
                elif env == "production" and self.log_level == "info":
                    # Production should use warning or error
                    self.log_level = "warning"
            # Set CORS defaults based on environment
            cors_env_set = os.getenv("CORS_ALLOW_ORIGINS") or os.getenv("CORS_ORIGINS")
            if not cors_env_set:
                if env == "development":
                    # Development: allow React frontend (Vite dev server)
                    default_origins = _split_csv(_DEFAULT_CORS)
                    if not self.cors_origins or self.cors_origins == default_origins:
                        self.cors_origins = [
                            "http://localhost:5173",  # Vite dev server (React frontend)
                            "http://127.0.0.1:5173",  # Vite dev server (alternative)
                        ]
                elif env == "production":
                    # Production: should be explicitly set, but default to empty
                    # (forces explicit configuration)
                    default_origins = _split_csv(_DEFAULT_CORS)
                    if not self.cors_origins or self.cors_origins == default_origins:
                        self.cors_origins = []
                        import warnings

                        warnings.warn(
                            "CORS_ALLOW_ORIGINS not set in production. "
                            "Please configure allowed origins explicitly.",
                            UserWarning,
                            stacklevel=2,
                        )
            return self

        @field_validator("log_level", mode="before")
        @classmethod
        def _normalize_log_level(cls, v: Any) -> str:
            """Normalize and validate log level."""
            if v is None:
                return "info"
            v = str(v).lower().strip()
            if v not in _ALLOWED_LOG_LEVELS:
                # default conservatively to info
                return "info"
            return v

        @field_validator("cors_origins", mode="before")
        @classmethod
        def _parse_cors(cls, v: Any) -> list[str]:  # accepts str | list[str]
            # If explicit value provided, honor it, else build from raw
            if v:
                return _split_csv(v)  # type: ignore[arg-type]
            return _split_csv(
                os.getenv("CORS_ALLOW_ORIGINS")
                or os.getenv("CORS_ORIGINS", _DEFAULT_CORS)
            )

        # Convenience: integer logging level for stdlib logging
        @property
        def log_level_int(self) -> int:
            return getattr(logging, self.log_level.upper(), logging.INFO)

else:

    class Settings(BaseModel):
        """Fallback settings without pydantic-settings.

        Reads directly from `os.environ`. Keep names aligned with the preferred
        model above so the rest of the code doesn't need to change.
        """

        app_name: str = Field(
            default_factory=lambda: os.getenv("API_TITLE")
            or os.getenv("APP_NAME", "ZenetHunter API")
        )
        app_version: str = Field(
            default_factory=lambda: os.getenv("API_VERSION")
            or os.getenv("APP_VERSION", "0.1.0")
        )
        app_env: str = Field(
            default_factory=lambda: os.getenv("APP_ENV", "development")
        )
        app_host: str = Field(default_factory=lambda: os.getenv("APP_HOST", "0.0.0.0"))
        app_port: int = Field(
            default_factory=lambda: int(os.getenv("APP_PORT", "8000"))
        )
        log_level: str = Field(
            default_factory=lambda: os.getenv("LOG_LEVEL", "info").lower()
        )
        secret_key: str = Field(
            default_factory=lambda: os.getenv(
                "SECRET_KEY", "insecure-dev-secret-key-do-not-use-in-production"
            )
        )
        database_url: str | None = Field(
            default_factory=lambda: os.getenv("DATABASE_URL")
        )
        cors_origins: list[str] = Field(
            default_factory=lambda: _split_csv(
                os.getenv("CORS_ALLOW_ORIGINS")
                or os.getenv("CORS_ORIGINS", _DEFAULT_CORS)
            )
        )

        # Integration: Router adapter selection & connection params (fallback)
        router_adapter: str = Field(
            default_factory=lambda: os.getenv("ROUTER_ADAPTER", "dummy").lower()
        )
        router_host: str | None = Field(
            default_factory=lambda: os.getenv("ROUTER_HOST")
        )
        router_port: int | None = Field(
            default_factory=lambda: (
                int(os.getenv("ROUTER_PORT")) if os.getenv("ROUTER_PORT") else None
            )
        )
        router_username: str | None = Field(
            default_factory=lambda: os.getenv("ROUTER_USERNAME")
        )
        router_password: str | None = Field(
            default_factory=lambda: os.getenv("ROUTER_PASSWORD")
        )

        # Active Scanning Configuration (fallback)
        scan_range: str = Field(
            default_factory=lambda: os.getenv("SCAN_RANGE", "192.168.1.0/24")
        )
        scan_timeout_sec: int = Field(
            default_factory=lambda: int(os.getenv("SCAN_TIMEOUT_SEC", "30"))
        )
        scan_concurrency: int = Field(
            default_factory=lambda: int(os.getenv("SCAN_CONCURRENCY", "10"))
        )
        scan_interval_sec: int | None = Field(
            default_factory=lambda: (
                int(os.getenv("SCAN_INTERVAL_SEC"))
                if os.getenv("SCAN_INTERVAL_SEC")
                else None
            )
        )

        # Feature Flags for Enrichment (fallback)
        feature_mdns: bool = Field(
            default_factory=lambda: os.getenv("FEATURE_MDNS", "true").lower() == "true"
        )
        feature_ssdp: bool = Field(
            default_factory=lambda: os.getenv("FEATURE_SSDP", "true").lower() == "true"
        )
        feature_nbns: bool = Field(
            default_factory=lambda: os.getenv("FEATURE_NBNS", "false").lower() == "true"
        )
        feature_snmp: bool = Field(
            default_factory=lambda: os.getenv("FEATURE_SNMP", "false").lower() == "true"
        )
        feature_fingerbank: bool = Field(
            default_factory=lambda: os.getenv("FEATURE_FINGERBANK", "false").lower()
            == "true"
        )

        # Integration: Webhook verification (fallback)
        webhook_secret: str = Field(
            default_factory=lambda: os.getenv("WEBHOOK_SECRET", "dev-webhook-secret")
        )
        webhook_tolerance_sec: int = Field(
            default_factory=lambda: int(os.getenv("WEBHOOK_TOLERANCE_SEC", "300"))
        )

        @property
        def log_level_int(self) -> int:
            return getattr(logging, self.log_level.upper(), logging.INFO)


# ---- public accessor --------------------------------------------------------
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance.

    FastAPI docs recommend caching to avoid repeatedly reading dotenv files
    or environment on every request while still allowing overrides in tests.
    """

    return Settings()  # type: ignore[call-arg]


# For ad‑hoc debugging: `python -m app.core.config`
if __name__ == "__main__":  # pragma: no cover
    s = get_settings()
    dump: dict[str, Any] = {
        "app_name": s.app_name,
        "app_version": s.app_version,
        "app_env": s.app_env,
        "app_host": s.app_host,
        "app_port": s.app_port,
        "log_level": s.log_level,
        "log_level_int": s.log_level_int,
        "database_url": bool(s.database_url),
        "cors_origins": s.cors_origins,
        "router_adapter": getattr(s, "router_adapter", "dummy"),
        "webhook_tolerance_sec": getattr(s, "webhook_tolerance_sec", 300),
    }
    import json

    print(json.dumps(dump, indent=2))
