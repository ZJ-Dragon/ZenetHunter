# API Contracts

This file records the REST and WebSocket contracts that agents should treat as stable unless a task explicitly requires a coordinated contract change.

## Base Endpoints
- REST base: `/api`
- WebSocket endpoint: `/api/ws`

## Authentication and Setup
- `POST /api/auth/login`
  - Form payload via `OAuth2PasswordRequestForm`
  - Returns `{ access_token, token_type }`
- `GET /api/config/status`
  - Returns OOBE flags: `admin_exists`, `first_run_completed`
- `POST /api/config/register`
  - Bootstraps the admin account on first run
- `POST /api/config/acknowledge`
  - Marks the first-run disclaimer complete
- `POST /api/config/replay`
  - Resets the system back toward first-run state
- `GET /api/config/platform`
  - Returns platform summary and capability data
- `GET /api/config/scan`
  - Returns effective scan configuration and feature flags

## Devices
- `GET /api/devices`
  - Returns `list[Device]`
- `GET /api/devices/{mac}`
  - Returns a single canonical `Device`
- `POST /api/devices`
  - Internal/scanner-oriented device upsert path
- `PATCH /api/devices/{mac}`
  - Alias/tags update path
- `POST /api/devices/{mac}/recognition/override`
  - Manual recognition override for vendor/model/type
- `PUT /api/devices/{mac}/manual-label`
  - Manual display-name/display-vendor labeling path
- `DELETE /api/devices/{mac}/manual-label`
  - Clears manual labeling/profile binding

## Active Defense
- `GET /api/active-defense/types`
- `POST /api/active-defense/{mac}/start`
- `POST /api/active-defense/{mac}/stop`
- Compatibility endpoints remain available at:
  - `POST /api/active-defense/devices/{mac}/attack`
  - `POST /api/active-defense/devices/{mac}/attack/stop`
  - `POST /api/devices/{mac}/attack`
  - `POST /api/devices/{mac}/attack/stop`

## Scan, Topology, Logs, and Observations
- `POST /api/scan/start`
- `GET /api/scan/status`
- `GET /api/topology`
- `GET /api/logs`
- `POST /api/logs`
- `GET /api/logs/system-info`
- `GET /api/devices/{mac}/observations`
- `GET /api/scan/{scan_run_id}/observations`

## Config Lists
- `GET /api/config/lists`
- `POST /api/config/lists/allow`
- `POST /api/config/lists/block`
- `DELETE /api/config/lists/{mac}`

## Contract Discipline
- Do not rename, remove, or redesign these paths casually.
- If a change is required, update AGENT bridge docs, source docs, and affected client code in the same task.
- Preserve compatibility endpoints unless the task explicitly includes a coordinated removal and migration plan.
