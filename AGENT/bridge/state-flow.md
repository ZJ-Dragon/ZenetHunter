# State Flow

## Auth and Setup Flow
1. Frontend checks setup state through `/api/config/status`
2. If setup is incomplete, user is routed to `/setup`
3. Admin registration occurs through `/api/config/register`
4. Login uses `/api/auth/login`
5. Token is persisted to `localStorage` and attached to API requests
6. Limited-admin client gating is tracked separately in `localStorage`

## Scan Flow
1. Frontend starts a scan with `POST /api/scan/start`
2. Backend scanner clears existing device cache before running a fresh scan
3. Scanner writes devices to the database and updates `StateManager`
4. Backend emits `scanStarted`, `deviceAdded`, `scanLog`, and `scanCompleted`
5. Frontend refreshes device/topology views from REST and WS events

## Device Label Flow
1. Operator submits manual labels through `PUT /api/devices/{mac}/manual-label`
2. Backend creates or updates a manual profile, binds it to the device, and writes audit logs
3. Repository conversion recalculates `display_name` and `display_vendor`
4. Backend updates `StateManager` and emits `deviceUpdated`
5. Frontend redraws affected views using display helpers

## Active Defense Flow
1. Frontend starts or stops operations through `/api/active-defense/{mac}/start|stop`
2. Backend service updates runtime state, persistence, audit logs, and websocket events
3. Backend emits `activeDefenseStarted`, `activeDefenseStopped`, and `activeDefenseLog`
4. Frontend views should treat operation state as event-driven but remain able to reload from REST

## Logs and Topology Flow
- Logs are stored in memory via `StateManager` and exposed through `/api/logs`
- Topology is rebuilt from database-backed devices synchronized into `StateManager`
- Observations are persisted and retrieved through dedicated repositories and routes

## State-Change Rule
When changing runtime behavior, make sure the following stay aligned:
- database state
- repository-to-domain conversion
- in-memory `StateManager`
- websocket payloads
- frontend display assumptions
