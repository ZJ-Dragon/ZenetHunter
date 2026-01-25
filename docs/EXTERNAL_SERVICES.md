# External Recognition Services

## Overview

ZenetHunter integrates with external recognition providers to improve device identification accuracy. This document describes each provider, their capabilities, limitations, and configuration.

## Providers

### 1. MACVendors (Vendor Lookup)

**Purpose**: Identify device vendor from MAC address OUI (Organizationally Unique Identifier).

**API**: https://api.macvendors.com

**Features**:
- No registration or API key required
- Free tier: up to 1,000 requests/day
- Rate limit: ~1 request/second recommended
- Privacy: Only OUI (first 3 octets) sent, not full MAC

**Limitations**:
- Vendor-level only (not specific model)
- Free tier has daily limit
- No device category/type information

**Usage**:
```python
# Automatically used when FEATURE_EXTERNAL_LOOKUP=true
# Sends only OUI (e.g., "00:11:22") for MAC "00:11:22:33:44:55"
```

**Configuration**:
- Enable: `FEATURE_EXTERNAL_LOOKUP=true`
- No API key needed

### 2. Fingerbank (Device Fingerprint)

**Purpose**: Identify device model, category, and manufacturer from combined fingerprint.

**API**: https://api.fingerbank.org

**Features**:
- Detailed device identification (model, category)
- Fingerprint-based (DHCP options, User-Agent, etc.)
- Higher accuracy than OUI-only lookup

**Limitations**:
- Requires API key (registration at https://fingerbank.org)
- Privacy: Sends combined fingerprint (higher exposure)
- Rate limit: 0.5 requests/second, 500 requests/day
- Default: Disabled

**Usage**:
```python
# Requires API key configuration
export FINGERBANK_API_KEY=your_key_here
export FEATURE_EXTERNAL_LOOKUP=true
```

**Configuration**:
- Enable: `FEATURE_EXTERNAL_LOOKUP=true` + `FINGERBANK_API_KEY=...`
- Privacy: Higher exposure (sends fingerprint data)

## Recognition Priority

When external lookups are enabled, recognition follows this priority:

1. **Local OUI lookup** (fastest, no network)
2. **Local DHCP fingerprint matching** (fast, no network)
3. **External vendor lookup** (MACVendors, if enabled)
4. **External device fingerprint** (Fingerbank, if enabled and has key)

Results are combined with weighted confidence scores.

## Rate Limits & Caching

### Rate Limits

- **MACVendors**: 1 QPS, 1000/day
- **Fingerbank**: 0.5 QPS, 500/day

The system enforces these limits automatically. Exceeding limits returns a rate limit error (does not crash).

### Caching

- **TTL**: 7 days
- **Max Size**: 1000 entries (LRU eviction)
- **Location**: `backend/data/cache/recognition_cache.json` (gitignored)
- **Privacy**: Cache keys are hashed (no plaintext MACs)

## Default Behavior

**External lookups are OFF by default.**

To enable:
1. Set `FEATURE_EXTERNAL_LOOKUP=true` (environment variable)
2. Or enable via UI Settings (admin only)

**Note**: Environment variable defaults to `false` (safe default). UI and software layers add "soft restrictions" on top. See [PRIVACY.md](PRIVACY.md) for details.

## API Endpoints

### Get Providers

```http
GET /api/recognition/providers
```

Returns list of available providers, their status, and limits.

### Update External Lookup Setting

```http
POST /api/recognition/settings/external-lookup
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "enabled": true
}
```

**Admin only**. Updates runtime setting (not persisted to environment).

## Troubleshooting

### Provider Not Working

1. Check `FEATURE_EXTERNAL_LOOKUP` is enabled
2. Check domain whitelist (should allow provider domain)
3. Check rate limits (may be throttled)
4. Check circuit breaker (may be open if provider is down)
5. Check audit logs for errors

### Rate Limit Errors

- Wait for rate limit window to reset
- Check cache (cached results don't count toward limit)
- Reduce scan frequency

### Fingerbank Not Enabled

- Ensure `FINGERBANK_API_KEY` is set
- Ensure `FEATURE_EXTERNAL_LOOKUP=true`
- Check provider status via `/api/recognition/providers`

## References

- [PRIVACY.md](PRIVACY.md): Privacy policy and data minimization
- [SECURITY.md](../SECURITY.md): Security policies and domain whitelist
- MACVendors API: https://macvendors.com/api
- Fingerbank API: https://fingerbank.org/api
