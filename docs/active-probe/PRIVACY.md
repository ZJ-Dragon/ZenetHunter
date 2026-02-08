# Active Probe Privacy & Redaction

This project captures probe observations for authorized research while keeping sensitive payloads out of persistent storage and logs.

## What we store
- **Key fields only**: small, whitelisted strings (e.g., `http_title`, `http_server`, SSDP manufacturer/model hints, short banners, mDNS service names).
- **Keywords**: normalized tokens derived from the key fields, plus **keyword_hits** from the dictionary (rule id, matched token, infer summary, confidence delta).
- **Summaries**: brief human-readable strings; no raw payloads.
- **Metadata**: protocol/module name, device MAC, optional `scan_run_id`, timestamp, redaction level.

## What we do **not** store
- Full packet payloads or binary blobs.
- Credentials, cookies, tokens, or host-identifying secrets.
- Arbitrary free-form responses beyond the sanitized key fields.

## Redaction & sanitization
- Strings are trimmed, newline-stripped, HTML-escaped, and truncated (typically ≤160 chars).
- Only whitelisted keys are persisted; everything else is dropped.
- Structured logging mirrors summaries only; detailed fields stay in the observation store.
- Keyword dictionary (`backend/app/data/keyword_dictionary.yaml`) is versioned in repo; matches are stored as `keyword_hits` (rule id, matched token, delta, inferred hints) without raw payload.

## Export & reproduction
- Observations can be exported as NDJSON (one JSON object per line) for offline analysis.
- Exports include only the sanitized fields listed above.

## Keyword dictionary
- Versioned YAML: `backend/app/data/keyword_dictionary.yaml` (tracked in git; contains only non-sensitive tokens).
- Schema: `version`, `updated`, `rules[]` (id, priority, match.any_contains/any_regex, infer.vendor/product/category/os, confidence_delta, notes).
- Loader validates the file at startup; an invalid or missing file logs a clear error and falls back to a no-dictionary mode (no hits, no confidence deltas applied).
- Stored hits include only rule id, matched token, infer summary, and delta—never raw payloads.

## Usage guidance
- Keep probes in authorized, controlled environments.
- Review observation exports before sharing externally.
- When adding new probe enrichers, ensure they feed sanitized key fields only and never persist raw payloads.
