"""Recognition provider endpoints and settings."""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recognition", tags=["Recognition"])


@router.get("/providers")
async def get_providers() -> dict:
    """
    External providers removed; return offline-only status.
    """
    return {
        "providers": [],
        "external_lookup_enabled": False,
        "oui_only_mode": True,
        "message": "External providers removed; offline-only recognition is active.",
    }
