# ZenetHunter API Documentation

Complete REST API reference for ZenetHunter Active Defense Platform.

**Base URL**: `http://localhost:8000/api`  
**API Version**: v2.0.0  
**Authentication**: JWT Bearer Token

---

## Table of Contents

1. [Authentication](#authentication)
2. [Active Defense](#active-defense)
3. [Device Management](#device-management)
4. [Network Scanning](#network-scanning)
5. [Topology](#topology)
6. [Logs](#logs)
7. [Configuration](#configuration)
8. [WebSocket](#websocket)
9. [Error Handling](#error-handling)

---

## Authentication

### Login

Authenticate and receive a JWT token.

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=your_password
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the Authorization header for all subsequent requests:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## Active Defense

### List Operation Types

Get all available active defense operation types.

```http
GET /active-defense/types
Authorization: Bearer {token}
```

**Response**:
```json
[
  {
    "id": "kick",
    "name": "KICK",
    "description": "WiFi Deauthentication - Disconnect device from wireless network"
  },
  {
    "id": "arp_flood",
    "name": "ARP_FLOOD",
    "description": "ARP Flooding - Stress test network ARP tables"
  },
  ...
]
```

### Start Operation

Initiate an active defense operation on a target device.

```http
POST /active-defense/{mac}/start
Authorization: Bearer {token}
Content-Type: application/json

{
  "type": "arp_flood",
  "duration": 120,
  "intensity": 5
}
```

**Path Parameters**:
- `mac` (string, required): Target device MAC address (format: `aa:bb:cc:dd:ee:ff`)

**Request Body**:
- `type` (string, required): Operation type (see [Operation Types](#operation-types))
- `duration` (integer, required): Duration in seconds (1-3600)
- `intensity` (integer, optional): Intensity level 1-10 (default: 5)

**Response** (202 Accepted):
```json
{
  "device_mac": "aa:bb:cc:dd:ee:ff",
  "status": "running",
  "message": "Active defense arp_flood initiated on aa:bb:cc:dd:ee:ff",
  "start_time": "2026-01-17T10:30:00Z"
}
```

**Error Response** (400 Bad Request):
```json
{
  "type": "validation_error",
  "title": "Request Validation Failed",
  "status": 400,
  "detail": "Invalid intensity value",
  "correlation_id": "req-12345"
}
```

### Stop Operation

Stop any active defense operation on a target device.

```http
POST /active-defense/{mac}/stop
Authorization: Bearer {token}
```

**Path Parameters**:
- `mac` (string, required): Target device MAC address

**Response** (200 OK):
```json
{
  "device_mac": "aa:bb:cc:dd:ee:ff",
  "status": "stopped",
  "message": "Active defense operation stopped by user"
}
```

### Operation Types

| Type | Layer | Description |
|------|-------|-------------|
| `kick` | WiFi | WiFi Deauthentication |
| `beacon_flood` | WiFi | WiFi Beacon Flooding |
| `block` | Network | ARP Spoofing |
| `arp_flood` | Network | ARP Flooding |
| `icmp_redirect` | Network | ICMP Redirect |
| `dhcp_spoof` | Protocol | DHCP Spoofing |
| `dns_spoof` | Protocol | DNS Spoofing |
| `mac_flood` | Bridge | MAC Address Flooding |
| `vlan_hop` | Bridge | VLAN Hopping |
| `port_scan` | Advanced | TCP/UDP Port Scanning |
| `traffic_shape` | Advanced | Traffic Shaping |

---

## Device Management

### List All Devices

Get all discovered network devices.

```http
GET /devices
Authorization: Bearer {token}
```

**Query Parameters**:
- `status` (string, optional): Filter by status (`online`, `offline`, `blocked`)
- `type` (string, optional): Filter by type (`router`, `pc`, `mobile`, `iot`, `unknown`)
- `limit` (integer, optional): Maximum results (default: 100)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response**:
```json
{
  "devices": [
    {
      "mac": "aa:bb:cc:dd:ee:ff",
      "ip": "192.168.1.100",
      "name": "iPhone-12",
      "vendor": "Apple Inc.",
      "model": "iPhone 12",
      "type": "mobile",
      "status": "online",
      "active_defense_status": "idle",
      "first_seen": "2026-01-17T08:00:00Z",
      "last_seen": "2026-01-17T10:30:00Z",
      "tags": ["trusted"],
      "alias": "John's iPhone"
    }
  ],
  "total": 15,
  "limit": 100,
  "offset": 0
}
```

### Get Device Details

Get detailed information about a specific device.

```http
GET /devices/{mac}
Authorization: Bearer {token}
```

**Response**:
```json
{
  "mac": "aa:bb:cc:dd:ee:ff",
  "ip": "192.168.1.100",
  "name": "iPhone-12",
  "vendor": "Apple Inc.",
  "model": "iPhone 12",
  "type": "mobile",
  "status": "online",
  "active_defense_status": "idle",
  "first_seen": "2026-01-17T08:00:00Z",
  "last_seen": "2026-01-17T10:30:00Z",
  "tags": ["trusted"],
  "alias": "John's iPhone",
  "vendor_guess": "Apple",
  "model_guess": "iPhone 12",
  "recognition_confidence": 95,
  "recognition_evidence": {
    "sources": ["oui", "mdns", "dhcp"],
    "matched_fields": ["vendor", "hostname", "device_type"]
  }
}
```

### Update Device

Update device information (alias, tags, etc.).

```http
PATCH /devices/{mac}
Authorization: Bearer {token}
Content-Type: application/json

{
  "alias": "John's iPhone",
  "tags": ["trusted", "personal"]
}
```

**Response**:
```json
{
  "mac": "aa:bb:cc:dd:ee:ff",
  "alias": "John's iPhone",
  "tags": ["trusted", "personal"],
  "updated_at": "2026-01-17T10:35:00Z"
}
```

### Delete Device

Remove a device from the database.

```http
DELETE /devices/{mac}
Authorization: Bearer {token}
```

**Response** (204 No Content)

---

## Network Scanning

### Start Network Scan

Initiate a network scan to discover devices.

```http
POST /scan/start
Authorization: Bearer {token}
Content-Type: application/json

{
  "type": "quick",
  "target_subnets": ["192.168.1.0/24"]
}
```

**Request Body**:
- `type` (string, required): Scan type (`quick`, `deep`, `custom`)
- `target_subnets` (array, optional): Specific subnets to scan

**Response** (202 Accepted):
```json
{
  "scan_id": "scan-uuid-12345",
  "status": "running",
  "type": "quick",
  "started_at": "2026-01-17T10:40:00Z"
}
```

### Get Scan Status

Check the status of a running scan.

```http
GET /scan/status
Authorization: Bearer {token}
```

**Response**:
```json
{
  "scan_id": "scan-uuid-12345",
  "status": "running",
  "progress": 65,
  "devices_found": 12,
  "started_at": "2026-01-17T10:40:00Z",
  "estimated_completion": "2026-01-17T10:42:00Z"
}
```

### Stop Scan

Stop a running network scan.

```http
POST /scan/stop
Authorization: Bearer {token}
```

**Response**:
```json
{
  "scan_id": "scan-uuid-12345",
  "status": "stopped",
  "devices_found": 12,
  "stopped_at": "2026-01-17T10:41:30Z"
}
```

---

## Topology

### Get Network Topology

Retrieve the network topology graph.

```http
GET /topology
Authorization: Bearer {token}
```

**Response**:
```json
{
  "nodes": [
    {
      "id": "aa:bb:cc:dd:ee:ff",
      "label": "iPhone-12",
      "type": "mobile",
      "ip": "192.168.1.100",
      "status": "online"
    },
    {
      "id": "11:22:33:44:55:66",
      "label": "Router",
      "type": "router",
      "ip": "192.168.1.1",
      "status": "online"
    }
  ],
  "edges": [
    {
      "source": "aa:bb:cc:dd:ee:ff",
      "target": "11:22:33:44:55:66",
      "type": "wireless"
    }
  ],
  "metadata": {
    "total_devices": 15,
    "total_connections": 14,
    "last_updated": "2026-01-17T10:45:00Z"
  }
}
```

---

## Logs

### Get Event Logs

Retrieve system and operation logs.

```http
GET /logs
Authorization: Bearer {token}
```

**Query Parameters**:
- `level` (string, optional): Filter by log level (`debug`, `info`, `warning`, `error`)
- `source` (string, optional): Filter by source (`scan`, `active_defense`, `auth`, etc.)
- `start_time` (string, optional): Start time (ISO 8601)
- `end_time` (string, optional): End time (ISO 8601)
- `limit` (integer, optional): Maximum results (default: 100)

**Response**:
```json
{
  "logs": [
    {
      "id": "log-uuid-12345",
      "timestamp": "2026-01-17T10:30:00Z",
      "level": "info",
      "source": "active_defense",
      "message": "主动防御执行中: arp_flood | 目标 aa:bb:cc:dd:ee:ff",
      "metadata": {
        "mac": "aa:bb:cc:dd:ee:ff",
        "operation_type": "arp_flood",
        "duration": 120
      }
    }
  ],
  "total": 450,
  "limit": 100,
  "has_more": true
}
```

---

## Configuration

### Get Configuration

Retrieve current system configuration.

```http
GET /config
Authorization: Bearer {token}
```

**Response**:
```json
{
  "scan": {
    "default_timeout": 2,
    "max_concurrency": 50,
    "auto_scan_interval": 300
  },
  "active_defense": {
    "max_duration": 3600,
    "default_intensity": 5,
    "allowed_operations": ["arp_flood", "block", "kick"]
  },
  "security": {
    "require_auth": true,
    "session_timeout": 3600,
    "max_login_attempts": 5
  }
}
```

### Update Configuration

Update system configuration.

```http
PATCH /config
Authorization: Bearer {token}
Content-Type: application/json

{
  "scan": {
    "max_concurrency": 100
  }
}
```

**Response**:
```json
{
  "updated": true,
  "configuration": {
    "scan": {
      "max_concurrency": 100
    }
  },
  "updated_at": "2026-01-17T10:50:00Z"
}
```

---

## WebSocket

### Connection

Connect to the WebSocket endpoint for real-time updates.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Authentication

Send authentication message after connection:

```javascript
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your-jwt-token'
}));
```

### Event Types

#### Active Defense Events

**Operation Started**:
```json
{
  "event": "activeDefenseStarted",
  "data": {
    "mac": "aa:bb:cc:dd:ee:ff",
    "type": "arp_flood",
    "duration": 120,
    "intensity": 5,
    "start_time": "2026-01-17T10:30:00Z"
  }
}
```

**Operation Log**:
```json
{
  "event": "activeDefenseLog",
  "data": {
    "level": "info",
    "message": "主动防御执行中: arp_flood | 目标 aa:bb:cc:dd:ee:ff",
    "mac": "aa:bb:cc:dd:ee:ff",
    "operation_type": "arp_flood",
    "timestamp": "2026-01-17T10:30:05Z"
  }
}
```

**Operation Stopped**:
```json
{
  "event": "activeDefenseStopped",
  "data": {
    "mac": "aa:bb:cc:dd:ee:ff",
    "timestamp": "2026-01-17T10:32:00Z"
  }
}
```

#### Scan Events

**Scan Started**:
```json
{
  "event": "scanStarted",
  "data": {
    "scan_id": "scan-uuid-12345",
    "type": "quick",
    "timestamp": "2026-01-17T10:40:00Z"
  }
}
```

**Device Discovered**:
```json
{
  "event": "deviceDiscovered",
  "data": {
    "mac": "aa:bb:cc:dd:ee:ff",
    "ip": "192.168.1.100",
    "vendor": "Apple Inc.",
    "timestamp": "2026-01-17T10:40:15Z"
  }
}
```

**Scan Completed**:
```json
{
  "event": "scanCompleted",
  "data": {
    "scan_id": "scan-uuid-12345",
    "devices_found": 15,
    "duration": 120,
    "timestamp": "2026-01-17T10:42:00Z"
  }
}
```

---

## Error Handling

All API errors follow RFC 7807 Problem Details format.

### Error Response Format

```json
{
  "type": "validation_error",
  "title": "Request Validation Failed",
  "status": 400,
  "detail": "Duration must be between 1 and 3600 seconds",
  "correlation_id": "req-12345",
  "errors": [
    {
      "field": "duration",
      "message": "Value must be between 1 and 3600"
    }
  ]
}
```

### Common Error Codes

| Status | Type | Description |
|--------|------|-------------|
| 400 | `validation_error` | Invalid request parameters |
| 401 | `authentication_error` | Missing or invalid authentication |
| 403 | `authorization_error` | Insufficient permissions |
| 404 | `not_found` | Resource not found |
| 409 | `conflict` | Resource conflict (e.g., operation already running) |
| 429 | `rate_limit_exceeded` | Too many requests |
| 500 | `internal_error` | Server internal error |
| 503 | `service_unavailable` | Service temporarily unavailable |

### Error Handling Best Practices

1. **Check Status Codes**: Always check HTTP status codes
2. **Use Correlation IDs**: Log correlation IDs for debugging
3. **Implement Retry Logic**: For 429 and 503 errors
4. **Validate Before Sending**: Validate parameters client-side
5. **Handle Timeouts**: Set appropriate request timeouts

---

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Authentication**: 10 requests per minute
- **Active Defense Operations**: 5 concurrent operations per user
- **Network Scans**: 1 concurrent scan per user
- **General API**: 100 requests per minute per user

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642416000
```

---

## Pagination

List endpoints support pagination:

```http
GET /devices?limit=20&offset=40
```

**Response Headers**:
```http
X-Total-Count: 150
X-Limit: 20
X-Offset: 40
Link: </devices?limit=20&offset=60>; rel="next"
```

---

## Versioning

API versioning is handled via the URL path:

- **Current**: `/api/v2/...` (default, can omit version)
- **Legacy**: `/api/v1/...` (deprecated)

---

## SDKs and Client Libraries

### Python

```python
from zenethunter import ZenetHunterClient

client = ZenetHunterClient(
    base_url="http://localhost:8000",
    username="admin",
    password="your_password"
)

# Start operation
response = client.active_defense.start(
    mac="aa:bb:cc:dd:ee:ff",
    type="arp_flood",
    duration=120
)

# List devices
devices = client.devices.list(status="online")
```

### JavaScript/TypeScript

```typescript
import { ZenetHunterClient } from 'zenethunter-js';

const client = new ZenetHunterClient({
  baseUrl: 'http://localhost:8000',
  token: 'your-jwt-token'
});

// Start operation
const response = await client.activeDefense.start({
  mac: 'aa:bb:cc:dd:ee:ff',
  type: 'arp_flood',
  duration: 120
});

// WebSocket connection
client.ws.on('activeDefenseLog', (data) => {
  console.log('Log:', data);
});
```

---

## Interactive API Documentation

Access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## Support and Resources

- **GitHub**: https://github.com/ZJ-Dragon/ZenetHunter
- **Documentation**: https://zenethunter.readthedocs.io
- **Issue Tracker**: https://github.com/ZJ-Dragon/ZenetHunter/issues

---

**⚠️ Security Notice**: This API provides access to powerful network security research tools. Ensure proper authentication, authorization, and audit logging for all operations. Unauthorized use may violate laws and regulations.
