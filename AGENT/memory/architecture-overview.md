# Architecture Overview

## Top-Level Shape
ZenetHunter is a monorepo with three major layers:
- `backend/`: FastAPI application, domain models, persistence, services, active-defense engine integration, and WebSocket broadcasting
- `frontend/`: React/Vite SPA with route-driven operator workflows and live updates from the backend
- `docs/`: product, API, active-defense, setup, and privacy documentation

## Backend Structure
- `app/main.py` composes the FastAPI app, middleware, API router, and shutdown behavior
- `app/routes/` exposes REST and WebSocket entrypoints
- `app/services/` implements scan orchestration, active-defense orchestration, setup/reset, recognition, manual-profile flows, and websocket delivery
- `app/repositories/` owns database-facing persistence logic and domain-model conversion
- `app/models/` defines API/domain objects; `app/models/db/` defines SQLAlchemy storage models
- `app/core/` contains config, DB bootstrapping, middleware, logging, platform detection, security, and engine factories

## Frontend Structure
- `src/main.tsx` wires theme application, i18n, auth context, WebSocket context, toast provider, and router
- `src/router.tsx` defines login, setup, shell, and page routes
- `src/contexts/` owns authentication state and WebSocket lifecycle
- `src/lib/services/` wraps backend API calls
- `src/pages/` holds route-level operator views
- `src/components/` holds shell, shared UI, topology, logs, auth, and action controls
- `src/locales/` contains translation resources

## Core Runtime Flow
1. Operator loads the SPA and theme/i18n bootstrap occurs.
2. Auth context restores token state from local storage and the API client attaches bearer auth.
3. Frontend reads setup/config/auth status and renders setup, login, or the main shell.
4. Device inventory, logs, topology, observations, and active-defense controls call REST endpoints under `/api/*`.
5. WebSocket events from `/api/ws` refresh device, scan, log, and active-defense state in near real time.
6. Backend services coordinate persistence in repositories, in-memory projection in `StateManager`, and event delivery through `ConnectionManager`.

## Important Dual-State Pattern
The backend keeps both:
- Persistent storage in the database
- A lightweight in-memory projection in `StateManager`

Many UI-visible behaviors depend on both staying aligned. Changes that update persistence but skip state updates, or vice versa, are high-risk.
