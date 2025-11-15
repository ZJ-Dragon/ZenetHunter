"""Health check endpoints.

This module provides health probe endpoints for container orchestration
and monitoring systems (e.g., Kubernetes, Docker healthchecks).
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Kubernetes-style health probe endpoint.

    Returns:
        dict: A simple status response indicating the service is healthy.

    Example:
        GET /healthz -> 200 OK {"status": "ok"}
    """
    return {"status": "ok"}

