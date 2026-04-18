# Frontend Map

## Primary Runtime Tree
- `frontend/src/main.tsx`
  - Root bootstrap for theme, i18n, auth, websocket, router, and toasts
- `frontend/src/router.tsx`
  - Route table for setup, login, shell, and page views
- `frontend/src/contexts/`
  - Auth session state and WebSocket lifecycle
- `frontend/src/pages/`
  - Route-level pages: dashboard, devices, topology, attacks, logs, settings, login, setup, not found
- `frontend/src/components/`
  - Shared UI primitives, shell, auth wrappers, actions, logs, topology detail panes
- `frontend/src/lib/services/`
  - REST client wrappers
- `frontend/src/types/`
  - Client-facing TypeScript types and event enums
- `frontend/src/locales/`
  - Translation resources

## Shared UI Areas
- `components/layout/`
  - App shell and navigation framing
- `components/ui/`
  - Buttons, surfaces, badges, dialogs, loading states, headers, toasts
- `components/actions/`
  - Scan, active-defense, and scheduler controls
- `components/topology/`
  - Graph rendering and node detail drawer
- `components/logs/`
  - Realtime log presentation

## Frontend State and Persistence
- Auth token and limited-admin flag live in `localStorage`
- Theme, locale, and platform preference also live in `localStorage`
- WebSocket connection status is in-memory in React context only

## Watchouts
- Some frontend service/type files still reference legacy field or endpoint names
- Do not assume a local UI label or type name matches the backend contract without checking AGENT bridge docs
