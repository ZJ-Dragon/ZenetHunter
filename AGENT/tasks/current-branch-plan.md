# Branch Plan: `refactor/backend-foundation`

## Objective
Refactor the backend into a stable layered architecture with replaceable low-level capability interfaces while keeping the implementation in Python and preserving existing API contracts unless a bridge-documented bug fix requires otherwise.

## Hard Constraints
- Read and follow `AGENT/` before changing backend code.
- Keep the current project in Python; do not introduce Rust in this branch.
- Preserve REST and WebSocket contracts unless a real bug fix requires a coordinated bridge update.
- Keep frontend API consumption stable.
- Treat backend-generated `display_name` and `display_vendor` as the single source of truth.
- Keep repository-local safety context local to this repository only.

## Confirmed Structural Problems To Fix
- Scan orchestration currently mixes hybrid candidate refresh and full discovery flows without a single source of truth, which can produce `scanCompleted` with `devices_found == 0` even after candidate confirmation.
- Scanner status is not consistently updated to final completed/failed values after the background task finishes.
- Capability detection is fragmented across platform detection, scanner capability checks, and attack-engine factory logic, so `scapy unavailable` / permission state is not exposed coherently.
- `routes/devices.py` mutates domain models as if they were ORM models and calls `db.refresh()` on non-ORM objects.
- Backend/frontend naming drift exists around `active_defense_status`, scan status routes, and other legacy compatibility assumptions.

## Planned Subtasks
1. Establish layered backend structure and shared contracts:
   - add application/domain/provider/bootstrap packages
   - define `DiscoveryProvider`, `ProbeProvider`, `FingerprintExtractor`, `DefenseExecutor`, and `CapabilityProvider`
   - add backend architecture notes to AGENT if contracts move
2. Refactor lifecycle and capability reporting:
   - isolate app/bootstrap wiring from `main.py`
   - unify capability detection and provider selection
   - expose coherent low-level capability state/reason without breaking current endpoints
3. Refactor scan orchestration:
   - make the scan pipeline explicit:
     `scan run -> observations -> fingerprint/key-field extraction -> device upsert -> manual profile match -> display field generation -> websocket refresh`
   - remove duplicated/contradictory scan paths
   - fix `scan completed but devices == 0`
   - fix final scan status updates
4. Refactor recognition/manual/display pipeline:
   - move display-field generation and manual-profile matching into backend orchestration/domain logic
   - keep `display_name` / `display_vendor` canonical
   - fix device/manual sync issues and broken device update routes
5. Refactor defense execution and provider abstraction:
   - wrap current Scapy/dummy behavior behind `DefenseExecutor`
   - keep active-defense routes stable
   - surface coherent availability and reason for scapy / permission state
6. Bridge synchronization and cleanup:
   - update AGENT bridge docs if any event/payload/capability fields change
   - run validation, fix regressions, and note follow-up items

## Execution Order
- Complete one subtask at a time.
- Commit and push after each subtask.
- Keep each commit subject at or below 88 characters.
- After every 2-3 subtasks run:
  - `pre-commit run --all-files`
  - backend tests
  - frontend tests if bridge-visible backend behavior changed
  - CI status check

## Validation Targets
- Existing backend test suite under `backend/tests`
- Frontend smoke test suite under `frontend`
- Manual verification of:
  - platform/capability reporting
  - scan status progression
  - device display-field generation
  - WebSocket event stability

## Progress Snapshot
- Completed: Subtask 1 (`refactor(backend): add layered bootstrap and provider contracts`)
- Completed: Subtask 2 (`refactor(backend): unify capability reporting and defense execution`)
- Completed: Subtask 3 (explicit scan orchestration, shared scanner singleton, candidate fallback, final scan status updates)
- Completed: Subtask 4 (recognition/manual/display pipeline cleanup and broken device routes)
- Completed: Subtask 5 (defense executor abstraction and coherent capability reporting)
- Completed: Subtask 6 (bridge synchronization, legacy compatibility aliasing, validation pass)
- Completed: Subtask 7 (active-defense/state-sync convergence and false event suppression)
- Completed: Subtask 8 (merged persisted/runtime logs and recognition route repair)
- Completed: Subtask 9 (frontend stale adapter removal and canonical websocket sync)

## Remaining Follow-up
- Frontend still reads the legacy compatibility alias `attack_status` in a few places even though the backend canonical field is `active_defense_status`.
- CI still only triggers on `push` to `main` and `pull_request` targeting `main`; branch pushes require manual local validation.

## Stabilization Pass: 2026-04-19

### Newly Confirmed Drift / Broken Spots
- Active-defense status does not fully round-trip through database, `StateManager`, and WebSocket events when an operation finishes naturally or fails in the background task.
- `topology` and several device mutation routes synchronize database-backed devices into `StateManager` with event emission still enabled, which can create false `deviceAdded` / `deviceStatusChanged` broadcasts during read-only refresh flows.
- `/api/logs` only reads in-memory state while many runtime paths write audit data to `event_log`, so the logs page misses persisted events and restarts drop useful history.
- `routes/recognition.py` still carries a hard-coded `/api/recognition` prefix even though the root router already mounts everything under `/api`, producing a broken `/api/api/recognition/*` path.
- Frontend WebSocket listeners and service wrappers still miss canonical backend updates (`deviceUpdated`, `recognitionOverridden`, canonical scan status route, removed scheduler paths).
- Dead/stale frontend adapters (`schedulerService`, `SchedulerControl`, generic `deviceService.update()`/`delete()`) still point at removed backend routes.

### New Subtasks
7. Close active-defense and state-sync gaps:
   - move device status persistence and websocket/device refresh emission into the active-defense service lifecycle
   - prevent read-only state hydrations from emitting false device lifecycle events
   - make operation completion/failure/cancel paths converge on the same state update contract
8. Close logs and route drift:
   - make `/logs` return persisted audit logs together with in-memory runtime logs
   - persist POSTed logs through the repository path as well
   - fix the broken recognition router prefix and document any bridge-visible alignment changes
9. Remove stale frontend adapters and finish WS/frontend sync:
   - replace or remove dead service wrappers pointing at missing routes
   - subscribe dashboard/device/topology views to canonical backend update events
   - remove clearly dead scheduler UI/service code
