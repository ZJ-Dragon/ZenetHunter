# Known Risks

## Security-Sensitive Runtime Areas
- `backend/app/core/engine/` contains packet-level active-defense implementations and platform-specific engine selection
- `backend/app/core/security.py`, `backend/app/services/auth.py`, `backend/app/services/setup.py`, and `backend/app/services/reset.py` affect authentication, first-run gating, and replay/reset behavior
- `backend/app/routes/attack.py` and `backend/app/services/attack.py` control active-defense operations and their audit/event side effects

## State Drift Risks
- Device data lives in both the database and `StateManager`; partial updates can create stale topology, stale logs, or stale websocket behavior
- Manual labels, manual profiles, recognition data, and display helpers are assembled in repository conversion logic, not only in the frontend

## Frontend/Backend Alignment Risks
- Canonical backend field is `active_defense_status`, but parts of the frontend still use legacy `attack_status`
- `frontend/src/lib/services/device.ts` contains a generic `update()` helper that targets `PUT /devices/{mac}`, while the backend route currently exposes `PATCH /devices/{mac}` for alias/tags updates
- `frontend/src/lib/services/scan.ts` calls `GET /scan/{scanId}`, while the backend route exposes `GET /scan/status`
- `frontend/src/lib/services/scheduler.ts` references scheduler endpoints, but scheduler routes are not part of the current backend router set
- WebSocket payload coverage in frontend types is incomplete; backend emits additional events such as `deviceListCleared`, `scanLog`, and `recognitionOverridden`

## Operational Risks
- Scanner startup clears the device cache before a fresh scan
- WebSocket auth is weakly enforced at the endpoint level today; the frontend sends a token query param, but the endpoint does not currently validate it
- Replay/reset and first-run flows affect auth state, runtime data, and operator routing; changes here can lock users out or leave stale sessions behind

## Documentation Risks
- Root localized README variants are incomplete today and need explicit agent guidance
- If API or event contracts change without bridge-doc updates, later agents are likely to propagate drift
