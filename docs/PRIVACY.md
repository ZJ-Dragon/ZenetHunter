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

## Questions?

See [EXTERNAL_SERVICES.md](EXTERNAL_SERVICES.md) for provider details and [SECURITY.md](../SECURITY.md) for security policies.
