# High-Risk Zones

These areas should not be modified casually. They control authorization, sensitive runtime behavior, or cross-layer contracts.

## Backend High-Risk Zones
- `backend/app/core/security.py`
  - Auth dependencies and admin gating
- `backend/app/services/auth.py`
  - Token validation/creation
- `backend/app/services/setup.py`
  - First-run registration and login behavior
- `backend/app/services/reset.py`
  - Replay/reset semantics
- `backend/app/core/engine/`
  - Raw-packet active-defense implementations and platform-specific selection
- `backend/app/services/attack.py`
  - Operation orchestration, event emission, and audit effects
- `backend/app/services/scanner_service.py`
  - Device cache clearing, scan lifecycle, and scan event emission
- `backend/app/repositories/device.py`
  - Canonical device-domain assembly, manual-label binding, display helper generation
- `backend/app/services/state.py` and `backend/app/services/websocket.py`
  - Runtime projection and live event delivery

## Frontend High-Risk Zones
- `frontend/src/contexts/AuthContext.tsx`
  - Session restore/logout behavior
- `frontend/src/contexts/WebSocketContext.tsx`
  - Event subscription lifecycle and reconnect logic
- `frontend/src/lib/services/`
  - API path assumptions and client contract drift
- `frontend/src/types/device.ts` and `frontend/src/types/websocket.ts`
  - Type assumptions that affect every page
- `frontend/src/pages/Settings.tsx` and `frontend/src/pages/SetupWizard.tsx`
  - Setup, replay/reset, locale/theme/platform preferences

## Documentation High-Risk Zones
- Root `README*.md`
  - These are the main onboarding surfaces for humans and agents
- `docs/api/README*.md`
  - Public contract documentation
- `AGENT/bridge/*`
  - Repository-local contract memory for future agents

## High-Risk Rule
If a task touches one of these zones, review source, tests, and AGENT bridge docs before editing.
