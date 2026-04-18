"""ZenetHunter backend entrypoint (FastAPI)."""

from __future__ import annotations

import logging

from app.bootstrap import create_app
from app.core.config import get_settings

logger = logging.getLogger(__name__)

try:  # Optional in dev; avoid hard dependency at import time
    import uvicorn  # type: ignore
except Exception:  # pragma: no cover
    uvicorn = None  # type: ignore

settings = get_settings()
app = create_app()


# ---- Local dev entry --------------------------------------------------------
if __name__ == "__main__" and uvicorn is not None:  # pragma: no cover
    host = settings.app_host
    port = settings.app_port
    reload = settings.app_env == "development"
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)
