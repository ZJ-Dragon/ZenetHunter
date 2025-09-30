

# syntax=docker/dockerfile:1.6

# ------------------------------------------------------------
# 1) Builder stage: create an isolated venv and install deps
#    Using the official Python slim image keeps the base small.
#    Ref: Docker multi-stage builds & best practices
# ------------------------------------------------------------
FROM python:3.12-slim AS builder

# Prevent Python from writing .pyc and force unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Workdir inside the image
WORKDIR /app

# Create a virtual environment for runtime deps (keeps system Python clean)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install build tools that pip may need (wheel)
RUN pip install --no-cache-dir --upgrade pip wheel

# Copy backend project (pyproject + sources) and install it
# Note: installing the project (.) ensures dependencies in pyproject.toml are resolved
# If you prefer to avoid packaging the app into site-packages, you can
# instead `pip install fastapi uvicorn[standard]` here and copy sources only.
COPY backend/ /app/
RUN pip install --no-cache-dir .


# ------------------------------------------------------------
# 2) Runtime stage: minimal image, non‑root user, copy venv + app
#    Ref: run as non‑root and keep runtime small
# ------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Same envs as builder (recommended for consistency)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

WORKDIR /app

# Create a non-root user and group
# Using fixed UID/GID can help with file permissions on certain NAS setups
RUN groupadd -r app && useradd -r -g app -u 10001 app

# Copy only what we need at runtime: venv (deps + installed app) and app sources
COPY --from=builder /opt/venv /opt/venv
COPY backend/app /app/app

# Adjust ownership
RUN chown -R app:app /app /opt/venv
USER app

# Expose the FastAPI port (for documentation purposes)
EXPOSE 8000

# Default command: run Uvicorn
# For multi-core CPUs you may set `--workers` via env or override the CMD in Compose
# See FastAPI docs: server workers with Uvicorn/Gunicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ------------------------------------------------------------
# Notes:
# - Healthcheck is defined in docker-compose.yml to avoid duplication.
# - If BuildKit is enabled, you may cache pip downloads with cache mounts:
#   (uncomment the syntax line >=1.6‑labs and RUN below)
#   RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
#   Docs: https://docs.docker.com/build/cache/optimize/
# ------------------------------------------------------------
