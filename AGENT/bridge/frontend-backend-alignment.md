# Frontend/Backend Alignment

## Canonical Source of Truth
- Backend route files under `backend/app/routes/` define the live HTTP surface
- Backend repositories and models define canonical payload shape
- Frontend service wrappers under `frontend/src/lib/services/` should be treated as consumers, not as the source of truth

## Stable Alignment Points
- API base is injected from `VITE_API_URL` and defaults to `http://localhost:8000/api`
- WebSocket URL is injected from `VITE_WS_URL` and defaults to `ws://localhost:8000/api/ws`
- Auth token is stored in `localStorage` key `token` and attached by the Axios interceptor
- Limited-admin client gating is tracked in `localStorage` key `limited_admin`

## Known Naming Drift
- Backend canonical field: `active_defense_status`
- Frontend legacy field usage still appears as `attack_status` in several pages/components
- Backend canonical terminology prefers "active defense"; frontend still uses "attack" in filenames, route names, and parts of the UI

## Known Service Drift
- Backend alias/tags update route is `PATCH /api/devices/{mac}`; frontend generic `deviceService.update()` currently targets `PUT /devices/{mac}`
- Backend scan status route is `GET /api/scan/status`; frontend `scanService.getScanStatus(scanId)` currently targets `GET /scan/{scanId}`
- Frontend scheduler service still exists, but scheduler routes are not exposed in the active backend router set

## Alignment Rule
When changing code:
- Prefer documenting and fixing drift conservatively rather than expanding it
- Do not assume a frontend helper is correct just because it exists
- Validate route shape against backend routes before refactoring clients
- If a legacy field is still consumed in the UI, add an adapter or coordinated fix instead of silently renaming backend payloads
