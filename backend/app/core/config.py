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
    from pydantic import BaseModel, Field, field_validator
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
            validation_alias="API_TITLE",  # Also accepts APP_NAME for backward compatibility
        )
        app_version: str = Field(
            default_factory=lambda: os.getenv("API_VERSION") or os.getenv("APP_VERSION", "0.1.0")
        )

        # Runtime
        app_env: Literal["development", "staging", "production"] = Field(
            default="development",
            validation_alias="APP_ENV",
        )
        app_host: str = Field(default="0.0.0.0", validation_alias="APP_HOST")
        app_port: int = Field(default=8000, validation_alias="APP_PORT")

        # Logging
        log_level: str = Field(default="info", validation_alias="LOG_LEVEL")

        # External services (optional in early project phases)
        database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")

        # CORS: comma‑separated list → list[str]
        cors_origins_raw: str = Field(
            default_factory=lambda: os.getenv("CORS_ALLOW_ORIGINS") or os.getenv("CORS_ORIGINS", _DEFAULT_CORS)
        )
        cors_origins: list[str] = Field(default_factory=list)

        # Model & source configuration
        model_config = SettingsConfigDict(
            # If you later add a real .env, set env_file=".env" (requires python-dotenv)
            extra="ignore",
        )

        @field_validator("log_level")
        @classmethod
        def _normalize_log_level(cls, v: str) -> str:
            v = (v or "").lower().strip()
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
                os.getenv("CORS_ALLOW_ORIGINS") or os.getenv("CORS_ORIGINS", _DEFAULT_CORS)
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
            default_factory=lambda: os.getenv("API_TITLE") or os.getenv("APP_NAME", "ZenetHunter API")
        )
        app_version: str = Field(
            default_factory=lambda: os.getenv("API_VERSION") or os.getenv("APP_VERSION", "0.1.0")
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
        database_url: str | None = Field(
            default_factory=lambda: os.getenv("DATABASE_URL")
        )
        cors_origins: list[str] = Field(
            default_factory=lambda: _split_csv(
                os.getenv("CORS_ALLOW_ORIGINS") or os.getenv("CORS_ORIGINS", _DEFAULT_CORS)
            )
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
    }
    import json

    print(json.dumps(dump, indent=2))
