# Manual Profile Refactor Plan

Goals:
- Preserve manual labels in a long-lived manual profile table and stop storing them on `devices`.
- Surface manual overrides as highest-priority display fields across API and UI.
- Keep local resets safe by clearing volatile device data while retaining manual profiles.

Task list:
1) Add `device_manual_profile` model/repository/service with fingerprint_key + match_keys support; migrate existing manual labels/overrides into it.
2) Add device bindings (`manual_profile_id`) and computed fields (`display_name`, `display_vendor`, `name_auto`, `vendor_auto`) to API responses and state.
3) Update manual label endpoints and scan/recognition pipeline to match/bind manual profiles (fingerprint_key > mac > match_keys) and emit display fields via WS/events.
4) Frontend: consume new display/manual fields; show manual values as primary with automatic values collapsed/secondary.
5) Startup reset: add local-only reset helper clearing devices + volatile tables (scan runs, observations, bindings) while preserving `device_manual_profile`; wire into `start-local.*`.
6) Tests + linters: add coverage for profile matching and migration, run `pre-commit run --all-files` and backend tests after every 2–3 tasks.

Notes:
- Keep deprecated columns (`name_manual`, `vendor_manual`) for migration/backward compatibility but stop using them for display.
- Record reset actions in event log; guard reset to `APP_ENV=development`.
