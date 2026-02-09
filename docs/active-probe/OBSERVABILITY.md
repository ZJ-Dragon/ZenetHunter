# Active Probe Observability

Observability adds a reproducible trail for probe/enrichment responses without storing raw payloads.

## Data flow
1. Probe/enrichment modules return structured hints (HTTP titles/servers, SSDP device info, mDNS service names, short banners).
2. The observation pipeline sanitizes/whitelists key fields, extracts keywords, builds a short summary, and stores a record in SQLite (`probe_observations`).
3. Event logs reference the observation ID for traceability.
4. APIs expose read-only views for UI/exports.

## Storage layout
- Table: `probe_observations`
  - `id` (UUID), `device_mac`, `scan_run_id`, `protocol`, `timestamp`
  - `key_fields` (JSON), `keywords` (JSON array), `keyword_hits` (JSON array), `raw_summary` (TEXT), `redaction_level` (TEXT)
- Default local SQLite file: `./data/zenethunter.db` (WAL/SHM live alongside).
- WAL/SHM files are ignored from VCS; copy the DB + NDJSON exports for offline analysis.

## APIs
- `GET /api/devices/{mac}/observations?limit=&since=&format=ndjson|json`
- `GET /api/scan/{scan_run_id}/observations`
- NDJSON export is append-friendly for replay and external tooling.

## Frontend UX
- Topology device drawer: "Discovered Services" (mDNS/SSDP) and "Identification Hints" (HTTP/Printer/Banner) sections, collapsible by default to keep the canvas clean.
- Topology device drawer: “Probe Details / Observations” (collapsed by default). Shows protocol, time, keyword count summary; expanded view reveals key fields and keywords, with copy/export actions.
- Device list: per-row “More” (ellipsis) shows a compact observation preview and keyword hit count.
- Topology device drawer also includes a “Keyword Intelligence” card (collapsed by default): count + top inference summary in the header, full hit list (matched token, notes, delta, inferred vendor/product/os/category) when expanded.

## Keyword extraction & dictionary
- Keywords are normalized tokens derived from key fields.
- Dictionary file: `backend/app/data/keyword_dictionary.yaml` (versioned YAML).
  - Root keys: `version`, `updated`, `rules[]`.
  - Rule fields: `id`, `priority`, `match.any_contains[]` (lowercase), optional `match.any_regex[]` (reserved for a few precise cases), `infer.vendor/product/category/os`, `confidence_delta` (int), `notes` (one-liner).
  - Hits: `rule_id`, `matched_token`, `infer` + `infer_summary`, `confidence_delta`, `priority`, `notes`. Duplicate hits per rule within one observation are deduped.
- Priority & confidence: higher `priority` applies first; deltas sum then clamp to 0–100.
- Loader behavior: invalid/missing YAML logs a clear error and runs in no-dictionary mode (no hits applied).

## Reproduction
- Run a scan, then fetch observations by device or `scan_run_id`.
- Export NDJSON and keep the SQLite file to replay the same observation set.

## Operator tips
- Keep probe logging concise; avoid dumping raw responses to app logs.
- When adding new enrichers, route outputs through the observation pipeline (sanitize → keywords → summary → store).
