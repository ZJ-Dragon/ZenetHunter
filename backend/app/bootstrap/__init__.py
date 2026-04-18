"""Bootstrap package for application assembly and lifecycle wiring."""

from app.bootstrap.app_factory import create_app

__all__ = ["create_app"]
