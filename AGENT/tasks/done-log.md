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
