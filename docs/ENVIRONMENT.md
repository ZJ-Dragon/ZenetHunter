# Environment Variables Configuration

## Overview

ZenetHunter uses environment variables for configuration following the [12-Factor App](https://12factor.net/config) methodology. All configuration is loaded from environment variables, with optional support for `.env` files for local development.

## Environment File Location

### Primary Location: `.env` File

Create a `.env` file in the **backend directory** (`backend/.env`):

```bash
cd backend
touch .env
```

The application will automatically load variables from this file when using `pydantic-settings`.

### Alternative: System Environment Variables

You can also set environment variables directly in your shell:

```bash
# Linux/macOS
export APP_ENV=production
export APP_PORT=8000

# Windows (PowerShell)
$env:APP_ENV="production"
$env:APP_PORT="8000"
```

### Priority Order

1. **System environment variables** (highest priority)
2. **`.env` file** in `backend/` directory
3. **Default values** (lowest priority)

---

## Configuration Categories

### 1. Application Basics

#### `APP_ENV`
- **Type**: String
- **Default**: `development`
- **Values**: `development`, `staging`, `production`
- **Description**: Application environment. Affects logging level and CORS defaults.
- **Example**:
  ```bash
  APP_ENV=production
  ```

#### `API_TITLE` / `APP_NAME`
- **Type**: String
- **Default**: `ZenetHunter API`
- **Description**: Application name displayed in API documentation.
- **Example**:
  ```bash
  API_TITLE=ZenetHunter Network Scanner
  ```

#### `API_VERSION` / `APP_VERSION`
- **Type**: String
- **Default**: `0.1.0`
- **Description**: Application version.
- **Example**:
  ```bash
  API_VERSION=1.0.0
  ```

#### `APP_HOST`
- **Type**: String
- **Default**: `0.0.0.0`
- **Description**: Host address to bind the server.
- **Example**:
  ```bash
  APP_HOST=0.0.0.0  # Listen on all interfaces
  APP_HOST=127.0.0.1  # Listen only on localhost
  ```

#### `APP_PORT`
- **Type**: Integer
- **Default**: `8000`
- **Description**: Port number for the API server.
- **Example**:
  ```bash
  APP_PORT=8000
  ```

---

### 2. Logging

#### `LOG_LEVEL`
- **Type**: String
- **Default**: `info` (auto-adjusted by `APP_ENV`)
- **Values**: `debug`, `info`, `warning`, `error`, `critical`
- **Description**: Logging verbosity level.
  - **Development**: Defaults to `debug`
  - **Staging**: Defaults to `info`
  - **Production**: Defaults to `warning`
- **Example**:
  ```bash
  LOG_LEVEL=debug  # Show all logs including debug messages
  LOG_LEVEL=warning  # Show only warnings and errors
  ```

---

### 3. Security

#### `SECRET_KEY`
- **Type**: String
- **Default**: `insecure-dev-secret-key-do-not-use-in-production`
- **Description**: Secret key for cryptographic operations. **MUST be changed in production!**
- **Example**:
  ```bash
  SECRET_KEY=your-super-secret-key-here-min-32-chars
  ```
- **⚠️ Warning**: Never use the default value in production. Generate a secure random key:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

#### `ACTIVE_DEFENSE_ENABLED`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Global kill-switch for active defense operations. Must be explicitly enabled.
- **Example**:
  ```bash
  ACTIVE_DEFENSE_ENABLED=true  # Enable active defense
  ACTIVE_DEFENSE_ENABLED=false  # Disable (safe default)
  ```

#### `ACTIVE_DEFENSE_READONLY`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Read-only mode: allows querying active defense status but prevents execution.
- **Example**:
  ```bash
  ACTIVE_DEFENSE_READONLY=true  # Query only, no execution
  ```

#### `CORS_ALLOW_ORIGINS` / `CORS_ORIGINS`
- **Type**: String (comma-separated)
- **Default**: `http://localhost:5173` (development)
- **Description**: Allowed CORS origins for frontend access. Comma-separated list.
- **Example**:
  ```bash
  # Single origin
  CORS_ALLOW_ORIGINS=http://localhost:5173
  
  # Multiple origins
  CORS_ALLOW_ORIGINS=http://localhost:5173,https://zenethunter.example.com
  
  # Production (must be explicitly set)
  CORS_ALLOW_ORIGINS=https://zenethunter.example.com
  ```

---

### 4. Database

#### `DATABASE_URL`
- **Type**: String (SQLAlchemy connection string)
- **Default**: `None` (uses SQLite in `backend/data/`)
- **Description**: Database connection URL. If not set, uses SQLite.
- **Examples**:
  ```bash
  # SQLite (default, no configuration needed)
  # Database file: backend/data/zenethunter.db
  
  # PostgreSQL
  DATABASE_URL=postgresql://user:password@localhost:5432/zenethunter
  
  # MySQL
  DATABASE_URL=mysql+pymysql://user:password@localhost:3306/zenethunter
  
  # SQLite (explicit)
  DATABASE_URL=sqlite:///./data/zenethunter.db
  ```

---

### 5. Router Integration

#### `ROUTER_ADAPTER`
- **Type**: String
- **Default**: `dummy`
- **Values**: `dummy`, `xiaomi`, `tp-link`, etc.
- **Description**: Router adapter type for integration.
- **Example**:
  ```bash
  ROUTER_ADAPTER=xiaomi
  ```

#### `ROUTER_HOST`
- **Type**: String
- **Default**: `None`
- **Description**: Router IP address or hostname.
- **Example**:
  ```bash
  ROUTER_HOST=192.168.31.1
  ROUTER_HOST=router.example.com
  ```

#### `ROUTER_PORT`
- **Type**: Integer
- **Default**: `None`
- **Description**: Router API port.
- **Example**:
  ```bash
  ROUTER_PORT=8080
  ```

#### `ROUTER_USERNAME`
- **Type**: String
- **Default**: `None`
- **Description**: Router API username.
- **Example**:
  ```bash
  ROUTER_USERNAME=admin
  ```

#### `ROUTER_PASSWORD`
- **Type**: String
- **Default**: `None`
- **Description**: Router API password.
- **Example**:
  ```bash
  ROUTER_PASSWORD=your-router-password
  ```
- **⚠️ Security**: Consider using secrets management for production.

---

### 6. Webhook Configuration

#### `WEBHOOK_SECRET`
- **Type**: String
- **Default**: `dev-webhook-secret`
- **Description**: Secret for webhook signature verification.
- **Example**:
  ```bash
  WEBHOOK_SECRET=your-webhook-secret-key
  ```

#### `WEBHOOK_TOLERANCE_SEC`
- **Type**: Integer
- **Default**: `300` (5 minutes)
- **Description**: Time tolerance in seconds for webhook timestamp validation.
- **Example**:
  ```bash
  WEBHOOK_TOLERANCE_SEC=300
  ```

---

### 7. Scanning Configuration

#### `SCAN_MODE`
- **Type**: String
- **Default**: `hybrid`
- **Values**: `hybrid`, `full`
- **Description**: Scan mode.
  - `hybrid`: Cache-based scanning (fast, uses ARP/DHCP cache)
  - `full`: Full subnet scanning (slower, comprehensive)
- **Example**:
  ```bash
  SCAN_MODE=hybrid  # Recommended for most use cases
  SCAN_MODE=full  # Full subnet scan
  ```

#### `SCAN_ALLOW_FULL_SUBNET`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Allow full subnet scanning (high resource usage).
- **Example**:
  ```bash
  SCAN_ALLOW_FULL_SUBNET=true  # Enable full subnet scans
  ```

#### `SCAN_RANGE`
- **Type**: String (CIDR notation)
- **Default**: `192.168.1.0/24`
- **Description**: CIDR range for full subnet scanning (advanced mode only). Usually auto-detected from network.
- **Example**:
  ```bash
  SCAN_RANGE=192.168.31.0/24
  SCAN_RANGE=10.0.0.0/16
  ```

#### `SCAN_TIMEOUT_SEC`
- **Type**: Integer
- **Default**: `30`
- **Description**: Full scan timeout in seconds.
- **Example**:
  ```bash
  SCAN_TIMEOUT_SEC=60  # Increase timeout for large networks
  ```

#### `SCAN_CONCURRENCY`
- **Type**: Integer
- **Default**: `10`
- **Description**: Maximum concurrent probes for full scan.
- **Example**:
  ```bash
  SCAN_CONCURRENCY=20  # Increase for faster scanning (more CPU/network)
  ```

#### `SCAN_INTERVAL_SEC`
- **Type**: Integer or empty
- **Default**: `None` (manual scans only)
- **Description**: Interval in seconds for periodic automatic scans. Set to `None` or empty for manual-only.
- **Example**:
  ```bash
  SCAN_INTERVAL_SEC=300  # Auto-scan every 5 minutes
  # Leave unset for manual scans only
  ```

#### `SCAN_REFRESH_WINDOW`
- **Type**: Integer
- **Default**: `10`
- **Description**: Candidate refresh window in seconds (for hybrid mode).
- **Example**:
  ```bash
  SCAN_REFRESH_WINDOW=10
  ```

#### `SCAN_REFRESH_CONCURRENCY`
- **Type**: Integer
- **Default**: `10`
- **Description**: Maximum concurrent refresh probes.
- **Example**:
  ```bash
  SCAN_REFRESH_CONCURRENCY=10
  ```

#### `SCAN_REFRESH_TIMEOUT`
- **Type**: Float
- **Default**: `1.0`
- **Description**: Refresh probe timeout per device in seconds.
- **Example**:
  ```bash
  SCAN_REFRESH_TIMEOUT=1.0
  ```

---

### 8. Feature Flags (Enrichment)

#### `FEATURE_MDNS`
- **Type**: Boolean
- **Default**: `true`
- **Description**: Enable mDNS (multicast DNS) enrichment for device discovery.
- **Example**:
  ```bash
  FEATURE_MDNS=true
  FEATURE_MDNS=false  # Disable mDNS
  ```

#### `FEATURE_SSDP`
- **Type**: Boolean
- **Default**: `true`
- **Description**: Enable SSDP/UPnP enrichment for device discovery.
- **Example**:
  ```bash
  FEATURE_SSDP=true
  ```

#### `FEATURE_NBNS`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Enable NBNS (NetBIOS Name Service) for Windows device discovery.
- **Example**:
  ```bash
  FEATURE_NBNS=true  # Enable for Windows networks
  ```

#### `FEATURE_SNMP`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Enable SNMP queries (requires credentials).
- **Example**:
  ```bash
  FEATURE_SNMP=true  # Requires SNMP credentials
  ```

#### `FEATURE_ACTIVE_PROBE`
- **Type**: Boolean
- **Default**: `true`
- **Description**: Enable active probing (HTTP, Telnet, SSH, Printer, IoT protocols). Simulates normal server connections to get device info.
- **Example**:
  ```bash
  FEATURE_ACTIVE_PROBE=true  # Enable active device probing
  FEATURE_ACTIVE_PROBE=false  # Disable (faster but less accurate)
  ```

#### `FEATURE_FINGERBANK`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Enable Fingerbank API for external device fingerprinting (requires API key).
- **Example**:
  ```bash
  FEATURE_FINGERBANK=true  # Requires FINGERBANK_API_KEY
  ```

---

### 9. External Recognition Providers

#### `FEATURE_EXTERNAL_LOOKUP`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Enable external recognition providers (MACVendors, Fingerbank). **Default: False (safe default)**. UI and software add soft restrictions.
- **Example**:
  ```bash
  FEATURE_EXTERNAL_LOOKUP=true  # Enable external lookups
  FEATURE_EXTERNAL_LOOKUP=false  # Disable (privacy-safe default)
  ```

#### `EXTERNAL_LOOKUP_OUI_ONLY`
- **Type**: Boolean
- **Default**: `true`
- **Description**: OUI-only mode: send only OUI prefix (first 3 octets), not full MAC. Privacy protection (default: True).
- **Example**:
  ```bash
  EXTERNAL_LOOKUP_OUI_ONLY=true  # Privacy mode (recommended)
  EXTERNAL_LOOKUP_OUI_ONLY=false  # Send full MAC (less private)
  ```

#### `FINGERBANK_API_KEY`
- **Type**: String
- **Default**: `None`
- **Description**: Fingerbank API key (required for Fingerbank provider). Get your key from [Fingerbank](https://www.fingerbank.org/).
- **Example**:
  ```bash
  FINGERBANK_API_KEY=your-fingerbank-api-key-here
  ```

---

## Example `.env` File

Create `backend/.env` with your configuration:

```bash
# Application
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=debug

# Security
SECRET_KEY=your-super-secret-key-here-min-32-chars
ACTIVE_DEFENSE_ENABLED=false
ACTIVE_DEFENSE_READONLY=false
CORS_ALLOW_ORIGINS=http://localhost:5173

# Database (optional, uses SQLite by default)
# DATABASE_URL=postgresql://user:password@localhost:5432/zenethunter

# Scanning
SCAN_MODE=hybrid
SCAN_ALLOW_FULL_SUBNET=false
SCAN_RANGE=192.168.31.0/24

# Feature Flags
FEATURE_MDNS=true
FEATURE_SSDP=true
FEATURE_ACTIVE_PROBE=true
FEATURE_EXTERNAL_LOOKUP=false
EXTERNAL_LOOKUP_OUI_ONLY=true

# External Recognition (optional)
# FINGERBANK_API_KEY=your-api-key-here
```

---

## Production Checklist

Before deploying to production, ensure:

- [ ] `APP_ENV=production`
- [ ] `SECRET_KEY` is set to a secure random value
- [ ] `CORS_ALLOW_ORIGINS` is explicitly set to your frontend domain(s)
- [ ] `LOG_LEVEL=warning` or `error`
- [ ] `ACTIVE_DEFENSE_ENABLED` is set appropriately
- [ ] `DATABASE_URL` is configured (if not using SQLite)
- [ ] All sensitive values (passwords, API keys) are stored securely

---

## Troubleshooting

### Variables Not Loading

1. **Check file location**: Ensure `.env` is in `backend/` directory
2. **Check syntax**: No spaces around `=` sign: `KEY=value` (not `KEY = value`)
3. **Check quotes**: Only use quotes if value contains spaces: `KEY="value with spaces"`
4. **Restart server**: Changes to `.env` require server restart

### Environment-Specific Defaults

Some variables have different defaults based on `APP_ENV`:
- **Development**: `LOG_LEVEL` defaults to `debug`, CORS allows `localhost:5173`
- **Production**: `LOG_LEVEL` defaults to `warning`, CORS must be explicitly set

### Verification

Check current configuration:
```bash
cd backend
python -m app.core.config
```

This will print the current settings (sensitive values are masked).

---

## References

- [12-Factor App: Config](https://12factor.net/config)
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [FastAPI Settings](https://fastapi.tiangolo.com/advanced/settings/)
