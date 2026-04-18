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
- In progress: Subtask 1 (layered package structure, provider interfaces, branch coordination refresh)
- Pending: Subtasks 2-6
