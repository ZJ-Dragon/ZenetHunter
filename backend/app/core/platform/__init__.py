"""Platform detection and platform-specific features."""

from app.core.platform.detect import (
    Platform,
    PlatformFeatures,
    get_platform_features,
    is_linux,
    is_macos,
    is_windows,
)

__all__ = [
    "Platform",
    "PlatformFeatures",
    "get_platform_features",
    "is_linux",
    "is_macos",
    "is_windows",
]
