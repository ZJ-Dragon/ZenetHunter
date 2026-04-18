# Backend Map

## Primary Runtime Tree
- `backend/app/main.py`
  - App composition, middleware, router mounting, startup/shutdown flow
- `backend/app/core/`
  - Config, database, exceptions, logging, middleware, security, platform and engine plumbing
- `backend/app/routes/`
  - REST and WebSocket entrypoints
- `backend/app/services/`
  - Business orchestration and runtime workflows
- `backend/app/repositories/`
  - Persistence logic and domain conversion
- `backend/app/models/`
  - API/domain models
- `backend/app/models/db/`
  - SQLAlchemy storage models

## Important Service Areas
- `services/scanner_service.py`
  - Scan orchestration and scan-related websocket broadcasts
- `services/attack.py`
  - Active-defense orchestration and event emission
- `services/setup.py` / `services/reset.py`
  - OOBE, auth bootstrap, replay/reset
- `services/manual_profile_service.py`
  - Long-lived manual labeling/profile binding
- `services/websocket.py`
  - Broadcast manager
- `services/state.py`
  - In-memory runtime projection used by topology and logs

## Data and Maintenance
- `backend/app/data/`
  - Bundled lookup data such as vendor dictionaries
- `backend/app/maintenance/`
  - Maintenance and reset utilities
- `backend/data/`
  - Runtime data used by backend workflows

## Tests
- `backend/tests/`
  - API, engine, scan, device, auth, observation, and websocket coverage
