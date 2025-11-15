"""API route modules.

This package contains FastAPI routers organized by feature domain.
Each router is defined in its own module and can be imported and mounted
to the main application via `app.include_router()`.

Example:
    from app.routes import health
    app.include_router(health.router)
"""
