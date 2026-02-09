# Active Probe Device Identification

## Overview
Active Probe is a device identification technique that simulates normal client connections and lets devices tell us who they are (vendor, model, firmware). All probes are read-only and time-bounded.

## How it works
The engine attempts several protocols in parallel:
1) **HTTP/HTTPS**: fetches web admin pages
2) **Telnet**: grabs banners
3) **SSH**: grabs banners
4) **Printer protocols**: IPP and LPD
5) **IoT**: CoAP `/.well-known/core`

## Supported probes
### HTTP/HTTPS
- **Ports**: 80, 8080, 443, 8443, 8000, 8888
- **Extracts**: `Server` header, `X-Powered-By`, HTML `<title>`, meta tags (`name="device"`, `name="model"`), and device hints in HTML comments.
- **Example**
  ```
  GET http://192.168.31.1/
  Server: TP-Link Router
  Title: TP-Link Router Admin - TL-WR940N
  ```

### Telnet banners
- **Ports**: 23, 2323
- **Extracts**: welcome banner (often includes vendor/model/firmware).
- **Example**
  ```
  Welcome to TP-Link Router
  Model: TL-WR940N
  Firmware: 1.0.0
  ```

### SSH banners
- **Port**: 22
- **Extracts**: SSH version string and vendor hints.
- **Example**
  ```
  SSH-2.0-Cisco-1.25  # identifies Cisco devices
  SSH-2.0-OpenSSH_7.9 # typical Linux/Unix hosts
  ```

### Printer protocols
- **IPP (631)**: Get-Printer-Attributes → model and vendor
- **LPD (515)**: job handshake to detect printer service

### IoT protocol
- **CoAP (5683)**: GET `/.well-known/core` → resource list and device hints

## Recognition priority
Active Probe outputs carry the **highest confidence (75–85%)** because they are device-self-reported:
1. Active Probe (HTTP/Telnet/SSH/Printer/IoT)
2. Local OUI and keyword/dictionary matches (~80%)
3. DHCP fingerprint (local, ~70%)

## Configuration
- Enable/disable via environment variables:
  ```bash
  FEATURE_ACTIVE_PROBE=true   # default
  FEATURE_ACTIVE_PROBE=false  # disable active probing
  ```
- Timeouts: ~2s per probe, ~3s overall per device (fast failover between ports).

## Sample extracted data
### HTTP response
```json
{
  "http_server": "TP-Link Router",
  "http_title": "TP-Link Router Admin - TL-WR940N",
  "http_port": 80,
  "http_status": 200
}
```

### Telnet banner
```json
{
  "telnet_banner": "Welcome to TP-Link Router\nModel: TL-WR940N"
}
```

### SSH banner
```json
{
  "ssh_banner": "SSH-2.0-Cisco-1.25",
  "ssh_vendor": "Cisco"
}
```

### Example final identification
```json
{
  "best_guess_vendor": "TP-Link",
  "best_guess_model": "TL-WR940N",
  "confidence": 85,
  "evidence": {
    "sources": ["active_probe_http"],
    "matched_fields": ["http_title", "http_server"]
  }
}
```

## Safety
- Read-only: GETs and banner reads only; no configuration changes.
- Time-boxed: per-probe timeouts prevent long hangs.
- Concurrency: probes run in parallel but are bounded per device.
- Error isolation: failures are contained and do not block other probes.

## Performance
- Parallel probing across supported ports/protocols.
- Fast failover when ports are closed.
- Typical per-device wall time: ~2–3 seconds (depends on device responsiveness).

## Typical devices
- **Routers**: Web UI (80/443), sometimes Telnet (23); vendor/model from title + Server header.
- **Printers**: IPP (631) and LPD (515); model from IPP attributes.
- **IoT**: Web UI or CoAP (5683); model from HTTP/CoAP responses.
- **Servers/PCs**: SSH (22) and HTTP (80/443); OS/vendor hints from banners.

## Troubleshooting
- If probes fail: firewall blocks, ports closed, auth required (401/403), or timeouts too short.
- Improve hit rate: extend timeouts for slow devices, verify open ports, check `active_probe` logs.

## Used with other methods
Active Probe complements mDNS, SSDP/UPnP, and local OUI/dictionary lookups. Results are merged with weighted confidence to choose the final identity.
