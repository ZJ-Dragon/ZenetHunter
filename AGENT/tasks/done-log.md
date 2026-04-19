# Done Log

## 2026-04-18
- Created `AGENT/tasks/current-branch-plan.md` and committed it as the first branch subtask
- Added AGENT protocol-layer documentation for project memory, bridge contracts, repository maps, workflow rules, safety context, backlog, and done tracking
- Updated root README onboarding to require reading `AGENT/` first and added missing localized root README variants for Japanese, Korean, and Russian
- Extracted backend bootstrap/lifecycle wiring and added layered package skeleton plus provider interface contracts for the backend-foundation refactor
- Added a unified runtime capability report and defense-executor adapter so low-level execution readiness and fallback reasons are reported coherently without breaking existing capability booleans
- Refactored the scan path into explicit discovery, probe, fingerprint, device upsert, manual-match, display, and websocket refresh stages behind `ScanWorkflowService`
- Added discovery/probe/fingerprint provider adapters plus device-domain identity helpers so low-level scan capabilities are replaceable without changing upper layers
- Fixed structural scan bugs by making `ScannerService` a shared singleton, updating final scan status consistently, and falling back to unconfirmed cached candidates instead of silently returning zero devices
- Added backend tests for scan-workflow persistence/display-field generation and hybrid-discovery candidate fallback
- Reworked `routes/devices.py` to update alias/tags and recognition overrides through repository methods instead of treating domain models as ORM rows
- Switched manual-label fingerprint matching to persisted fingerprint records and refreshed manual-profile-backed display fields in the same session
- Added legacy device payload compatibility for frontend consumers that still read `attack_status` while keeping `active_defense_status` canonical
- Fixed frontend capability display drift by normalizing `capability_state` into the legacy settings/logs badges instead of treating missing old keys as `false`
- Added runtime diagnostics for interpreter path, environment kind, and module imports so support issues can distinguish backend `.venv`, conda, and system Python cleanly
- Hardened `start-local.sh` to use the selected interpreter consistently for `pip`, maintenance tasks, uvicorn startup, runtime dependency checks, and optional macOS authorization relaunch
- Closed active-defense state drift by persisting final operation status from the service layer, emitting canonical `deviceUpdated` refresh events, and preventing read-only topology/device hydrations from creating false device lifecycle broadcasts
- Unified `/api/logs` around merged persisted audit logs plus runtime state logs and fixed the recognition router path back to `/api/recognition/*`
- Removed dead frontend scheduler adapters, aligned `deviceService`/`scanService` with canonical backend routes, and subscribed dashboard/device/topology views to canonical backend update events
