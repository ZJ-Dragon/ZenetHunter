# Privacy Policy: External Recognition Providers

## Overview

ZenetHunter supports optional external recognition providers to improve device identification accuracy. This document explains what data is sent, how to minimize exposure, and how to disable external lookups.

## External Lookups: Default OFF

**By default, external recognition lookups are DISABLED.** The system functions normally without external providers, using only local recognition methods (OUI tables, DHCP fingerprints, mDNS/SSDP).

## What Data is Sent?

### MACVendors Provider (Vendor Lookup)

- **Data Sent**: Only the OUI (first 3 octets of MAC address), e.g., `00:11:22`
- **Full MAC**: Never sent (privacy protection)
- **Example**: For MAC `00:11:22:33:44:55`, only `00:11:22` is sent
- **Privacy Level**: Low (OUI only, cannot identify specific device)
- **API**: https://api.macvendors.com (public, no registration required)

### Fingerbank Provider (Device Fingerprint)

- **Data Sent**: Combined device fingerprint (DHCP options, User-Agent, etc.)
- **Privacy Level**: High (more detailed fingerprint data)
- **Requires**: API key (registration at https://fingerbank.org)
- **Default**: Disabled (requires explicit configuration)

## Privacy Protection Features

### 1. OUI-Only Mode (Default: Enabled)

When `EXTERNAL_LOOKUP_OUI_ONLY=true` (default), only OUI prefixes are sent, never full MAC addresses.

### 2. Domain Whitelist

Only specific domains are allowed:
- `macvendors.com`, `api.macvendors.com`
- `api.fingerbank.org`

All other domains are blocked.

### 3. Rate Limiting

- **MACVendors**: 1 request/second, 1000 requests/day (free tier limit)
- **Fingerbank**: 0.5 requests/second, 500 requests/day

### 4. Caching

All lookup results are cached locally (7 days TTL) to minimize external requests. Cache directory: `backend/data/cache/` (gitignored).

### 5. Audit Logging

All external lookups are logged (sanitized):
- Provider name
- Query type (vendor/device)
- Success/failure status
- Cache hit/miss
- **No sensitive data** (no full MACs, no API keys, no fingerprint details)

## How to Disable External Lookups

### Method 1: Environment Variable (Recommended)

```bash
export FEATURE_EXTERNAL_LOOKUP=false
```

### Method 2: UI Settings

1. Go to Settings page
2. Find "External Lookup" section
3. Toggle OFF

### Method 3: Configuration File

Add to `.env`:
```
FEATURE_EXTERNAL_LOOKUP=false
```

## Minimizing Data Exposure

1. **Use OUI-Only Mode**: Keep `EXTERNAL_LOOKUP_OUI_ONLY=true` (default)
2. **Enable Only MACVendors**: Disable Fingerbank if not needed
3. **Monitor Audit Logs**: Check logs to see what's being sent
4. **Use Cache**: Let the cache build up to reduce external requests

## Security Considerations

- **No API Keys in Logs**: API keys are never logged
- **No Full MACs in Logs**: Only OUI hashes are logged
- **Domain Whitelist**: Prevents requests to unauthorized domains
- **Circuit Breaker**: Prevents cascading failures if provider is down
- **Timeout Protection**: Requests timeout after 5-10 seconds

## Compliance

External lookups comply with:
- **GDPR**: Minimal data (OUI only), user consent (explicit enable)
- **Privacy by Design**: Default OFF, opt-in only
- **Data Minimization**: Only necessary data is sent

## Manual Device Labeling

### Overview

ZenetHunter allows administrators to manually label devices with custom names and vendor information. This feature provides:

1. **User-Defined Labels**: Override automatic recognition with your own device names and vendor information
2. **Fingerprint-Based Reuse**: Manual labels can be automatically applied to similar devices
3. **Local-Only Storage**: All manual labels are stored in the local SQLite database

### Data Storage

Manual labels are stored in two tables:

1. **devices table**: Contains per-device manual overrides (`name_manual`, `vendor_manual`)
2. **manual_overrides table**: Contains fingerprint-based labels for reuse across devices

### Privacy Protection

**All manual labeling data is stored locally and never transmitted:**

- Labels are stored in the local SQLite database (`backend/data/zenethunter.db`)
- No external services are involved in manual labeling
- No synchronization with cloud services
- Data remains on your local machine

### Database File Protection

**The database is protected from version control:**

- `backend/data/*.db` - All SQLite database files
- `backend/data/*-wal` - SQLite Write-Ahead Log files
- `backend/data/*-shm` - SQLite Shared Memory files

These files are excluded from git via `.gitignore` to prevent:
- Accidental commit of device information
- Exposure of manually labeled device names
- Leakage of network topology data

### Audit Logging

All manual labeling operations are logged:
- Who made the change (username)
- When the change was made
- Which device was affected (MAC address)
- What labels were applied (without sensitive content)

### Clearing Manual Labels

To clear all manual labels:

1. **Per-Device**: Use the "Clear manual labels" button in the device detail drawer
2. **All Devices**: Delete the database file and restart the application

### Fingerprint Key Generation

When you manually label a device, a "fingerprint key" is generated from:
- DHCP options (Vendor Class Identifier, hostname patterns)
- mDNS service types
- SSDP server headers
- OUI prefix (as fallback)

This key enables automatic label application to similar devices. The key is:
- **One-way hash**: Cannot be reversed to original data
- **Non-identifying**: Does not contain MAC addresses or IPs
- **Local-only**: Stored in local database only

## Questions?

See [EXTERNAL_SERVICES.md](EXTERNAL_SERVICES.md) for provider details and [SECURITY.md](../SECURITY.md) for security policies.
