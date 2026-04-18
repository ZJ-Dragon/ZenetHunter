# Data and Storage

## Backend Persistence Models
Database storage models currently live under `backend/app/models/db/`:
- `app_setting`
- `device`
- `device_fingerprint`
- `device_manual_profile`
- `event_log`
- `manual_override`
- `probe_observation`
- `trust_list`
- `user_account`

## Backend Runtime State
- `StateManager` holds:
  - in-memory device projection
  - in-memory recent logs
  - allow list
  - block list
- This state is not a substitute for the database; it is a live projection used by topology, logs, and event broadcasting

## Bundled Data
- `backend/app/data/keyword_dictionary.yaml`
  - Keyword extraction and recognition support data
- `backend/app/data/vendors/`
  - Vendor-related data sources

## Frontend Local Storage
Current keys used by the frontend include:
- `token`
- `limited_admin`
- `locale`
- `theme`
- `platform`

## Environment and Configuration
- Backend settings are environment-driven through `app/core/config.py`
- Frontend API/WS endpoints are driven by `VITE_API_URL` and `VITE_WS_URL`

## Storage Discipline
- Do not change local-storage key names casually
- Do not change database model semantics without updating repositories, domain models, API docs, AGENT bridge docs, and any migration path
