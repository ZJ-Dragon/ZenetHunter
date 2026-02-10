"""Device recognition services with external provider support."""

from app.services.recognition.external_service_policy import (
    ExternalServicePolicy,
    get_external_service_policy,
)

__all__ = [
    "ExternalServicePolicy",
    "get_external_service_policy",
]
